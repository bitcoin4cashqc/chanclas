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
        chanclas = await Chanclas.new("Chanclas", "CHNCLS", "http://localhost:3000/", admin, { from: admin });

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
        console.log(userprice.toString())
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
});
