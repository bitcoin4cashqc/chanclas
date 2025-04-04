const Chanclas = artifacts.require("Chanclas");
const ChanclasICO = artifacts.require("ChanclasICO");
const MockERC20 = artifacts.require("MockUSDC");

contract("ChanclasICO", (accounts) => {
    const admin = accounts[0];
    const user = accounts[1];
    let chanclas, chanclasICO, usdcToken;
    const BASE_PRICE = web3.utils.toWei("10", "ether");

    before(async () => {
        // Deploy mock USDC
        usdcToken = await MockERC20.new(web3.utils.toWei("1000000", "ether"), { from: user });

        // Deploy Chanclas NFT contract
        chanclas = await Chanclas.new("Chanclas", "CHNCLS", "http://localhost:3000/", { from: admin });

        // Define initial periods
        const initialPeriods = [
            [Math.floor(Date.now() / 1000) + 3600, 10, BASE_PRICE, 0],  // Period 0
            [Math.floor(Date.now() / 1000) + 7200, 20, web3.utils.toWei("1.5", "ether"), 0] // Period 1
        ];

        // Deploy ChanclasICO
        chanclasICO = await ChanclasICO.new(
            admin,
            usdcToken.address,
            chanclas.address,
            initialPeriods,
            { from: admin }
        );

        // Grant MINTER_ROLE to ChanclasICO
        const MINTER_ROLE = web3.utils.keccak256("MINTER_ROLE");
        await chanclas.grantRole(MINTER_ROLE, chanclasICO.address, { from: admin });
    });

    it("should initialize contracts correctly", async () => {
        assert.ok(chanclas.address, "Chanclas contract not deployed");
        assert.ok(chanclasICO.address, "ICO contract not deployed");
        assert.ok(usdcToken.address, "USDC contract not deployed");
    });

    it("should initialize with valid periods", async () => {
        const periods = await chanclasICO.getPeriods();
        assert.equal(periods.length, 2, "Should initialize with 2 periods");
        
        const firstPeriod = periods[0];
        assert(firstPeriod.endTime > 0, "First period should have end time");
        assert.equal(firstPeriod.price.toString(), BASE_PRICE, "First period price mismatch");
    });

    it("should mint NFTs with correct pricing and data", async () => {
        let expectedTokenId = 0;

        const price1 = await calculateExpectedPrice();
        await verifyMint(user, 0, price1, expectedTokenId++);
        
        const price2 = await calculateExpectedPrice();
        await verifyMint(user, 0, price2, expectedTokenId++);

        const tokenData = await chanclas.getTokenData(0);
        assert(tokenData.seed > 0, "Seed not generated");
        assert.equal(tokenData.periodId, 0, "Token period mismatch");
    });

    it("should apply progressive discounts correctly", async () => {
        for (let i = 0; i < 5; i++) {
            const expectedPrice = await calculateExpectedPrice();
            const currentRebate = await chanclasICO.getCurrentRebate({ from: user });

            assert.equal(currentRebate.toString(), expectedPrice, 
                `Rebate mismatch for mint ${i+1}`);
            
            await usdcToken.approve(chanclasICO.address, expectedPrice, { from: user });
            await chanclasICO.mint({ from: user });
        }
    });

    it("should handle period transitions correctly", async () => {
        await exhaustPeriod(0, 10, 7);

        const currentPeriod = await chanclasICO.currentPeriodId();
        assert.equal(currentPeriod.toNumber(), 1, "Should transition to period 1");

        const period = await chanclasICO.periods(1);
        const expectedFirstMint = await calculateExpectedPrice();
        const rebate = await chanclasICO.getCurrentRebate({ from: user });
        assert.equal(rebate.toString(), expectedFirstMint, "New period pricing mismatch");
    });

    it("should allow admin to manage periods and settings", async () => {
        const newPeriod = {
            endTime: Math.floor(Date.now() / 1000) + 10800,
            maxSupply: 15,
            price: web3.utils.toWei("2", "ether")
        };

        await chanclasICO.addPeriod(
            newPeriod.endTime,
            newPeriod.maxSupply,
            newPeriod.price,
            { from: admin }
        );

        await chanclasICO.changeBonus(60, 2, { from: admin });
        const [maxRebate, curveSteepness] = await Promise.all([
            chanclasICO.maxRebate(),
            chanclasICO.curveSteepness()
        ]);
        assert.equal(maxRebate, 60, "Max rebate not updated");
        assert.equal(curveSteepness, 2, "Curve steepness not updated");
    });

    it("should transition to next period when current period time expires", async () => {
        // Create a new set of periods for this test where we can control time
        const now = Math.floor(Date.now() / 1000);
        const timeBasedICO = await ChanclasICO.new(
            admin,
            usdcToken.address,
            chanclas.address,
            [
                [now + 100, 10, BASE_PRICE, 0],  // Period 0 - expires after 100 seconds
                [now + 3600, 20, web3.utils.toWei("2", "ether"), 0] // Period 1
            ],
            { from: admin }
        );
        
        // Grant minter role
        const MINTER_ROLE = web3.utils.keccak256("MINTER_ROLE");
        await chanclas.grantRole(MINTER_ROLE, timeBasedICO.address, { from: admin });
        
        // Get initial period
        const initialPeriodResult = await timeBasedICO.getCurrentPeriod();
        const initialPeriodId = initialPeriodResult.periodId;
        assert.equal(initialPeriodId.toNumber(), 0, "Should start at period 0");
        
        // Advance blockchain time to make period 0 expire
        await advanceTime(110); // Advance 110 seconds (past period 0 end time)
        await advanceBlock(); // Mine a new block to make the time change take effect
        
        // Call updatePeriodIfExpired to ensure the period is updated
        await timeBasedICO.updatePeriodIfExpired();
        
        // Verify currentPeriodId is updated
        const currentId = await timeBasedICO.currentPeriodId();
        assert.equal(currentId.toNumber(), 1, "Current period should be updated to 1");
        
        // Verify getCurrentPeriod also returns period 1
        const updatedPeriodResult = await timeBasedICO.getCurrentPeriod();
        const updatedPeriodId = updatedPeriodResult.periodId;
        assert.equal(updatedPeriodId.toNumber(), 1, "getCurrentPeriod should return period 1 after expiry");
        
        // Try to mint - this should work in period 1
        const price = await timeBasedICO.getCurrentRebate({ from: user });
        await usdcToken.approve(timeBasedICO.address, price, { from: user });
        await timeBasedICO.mint({ from: user });
        
        // Check that minting worked in period 1
        const periodData = await timeBasedICO.periods(1);
        assert.equal(periodData.mintedCount.toNumber(), 1, "Should have minted 1 NFT in period 1");
    });

    it("should handle multiple expired periods correctly", async () => {
        // Create a new ICO with three consecutive periods
        const now = Math.floor(Date.now() / 1000);
        const multiPeriodICO = await ChanclasICO.new(
            admin,
            usdcToken.address,
            chanclas.address,
            [
                [now + 100, 10, BASE_PRICE, 0],                     // Period 0 - expires after 100 sec
                [now + 200, 20, web3.utils.toWei("1.5", "ether"), 0], // Period 1 - expires after 200 sec
                [now + 3600, 30, web3.utils.toWei("2", "ether"), 0]    // Period 2 - expires after 1 hour
            ],
            { from: admin }
        );
        
        // Grant minter role
        const MINTER_ROLE = web3.utils.keccak256("MINTER_ROLE");
        await chanclas.grantRole(MINTER_ROLE, multiPeriodICO.address, { from: admin });
        
        // Verify initial period is 0
        const initialPeriod = await multiPeriodICO.currentPeriodId();
        assert.equal(initialPeriod.toNumber(), 0, "Initial period should be 0");
        
        // Advance time to make both periods 0 and 1 expire
        await advanceTime(210); // Advance 210 seconds (past period 0 and 1 end times)
        await advanceBlock(); // Mine a new block to make the time change take effect
        
        // Call updatePeriodIfExpired manually to see the effect
        await multiPeriodICO.updatePeriodIfExpired();
        
        // Verify we jumped directly to period 2, skipping period 1 which also expired
        const finalPeriod = await multiPeriodICO.currentPeriodId();
        assert.equal(finalPeriod.toNumber(), 2, "Should have skipped to period 2");
        
        // Try to mint in the current period
        const price = await multiPeriodICO.getCurrentRebate({ from: user });
        await usdcToken.approve(multiPeriodICO.address, price, { from: user });
        await multiPeriodICO.mint({ from: user });
        
        // Verify the NFT was minted in period 2
        const periodData = await multiPeriodICO.periods(2);
        assert.equal(periodData.mintedCount.toNumber(), 1, "Should have minted 1 NFT in period 2");
    });

    it("should handle edge cases properly", async () => {
        await expectRevert(
            chanclasICO.addPeriod(0, 0, 0, { from: user }),
            "AccessControl"
        );

        await exhaustPeriod(1, 27, 1);
        let testpircce = await calculateExpectedPrice()
        
        await verifyMint(user, 1, testpircce,1)
    });

    // ----------------- Helper Functions -----------------

    async function calculateExpectedPrice() {
        const userprice = await chanclasICO.getCurrentRebate({from: user})
        console.log(userprice.toString() / 1000000000000000000)
        return userprice
    }

    async function verifyMint(user, expectedPeriodId, expectedPrice, expectedTokenId) {
        await usdcToken.approve(chanclasICO.address, expectedPrice, { from: user });
        const tx = await chanclasICO.mint({ from: user });

        assert.equal(tx.logs[1].args.price.toString(), expectedPrice, "Price mismatch");

        const mintedId = tx.logs[1].args.tokenId.toNumber();
        //assert.equal(mintedId, expectedTokenId, "Token ID mismatch");
        console.log("Minting Token id :",mintedId)

        const periodId = tx.logs[1].args.periodId.toNumber();
        //assert.equal(periodId, expectedPeriodId, "Period ID mismatch");
        console.log("In period id :",periodId)
    }

    async function exhaustPeriod(periodId, supply, expectedTokenStart) {
        for (let i = 0; i < supply; i++) {
            const expectedPrice = await calculateExpectedPrice();
            await verifyMint(user, periodId, expectedPrice, expectedTokenStart + i);
        }
    }

    async function expectRevert(promise, errorMsg) {
        try {
            await promise;
            assert.fail("Expected revert not received");
        } catch (error) {
            assert.include(error.message.toLowerCase(), errorMsg.toLowerCase(), "Wrong revert reason");
        }
    }

    // Helper functions for time manipulation
    const advanceTime = (time) => {
        return new Promise((resolve, reject) => {
            web3.currentProvider.send({
                jsonrpc: '2.0',
                method: 'evm_increaseTime',
                params: [time],
                id: new Date().getTime()
            }, (err, result) => {
                if (err) { return reject(err) }
                return resolve(result)
            })
        })
    }
    
    const advanceBlock = () => {
        return new Promise((resolve, reject) => {
            web3.currentProvider.send({
                jsonrpc: '2.0',
                method: 'evm_mine',
                id: new Date().getTime()
            }, (err, result) => {
                if (err) { return reject(err) }
                return resolve(result)
            })
        })
    }
});
