const Chanclas = artifacts.require("Chanclas");
const ChanclasICO = artifacts.require("ChanclasICO");
const IERC20 = artifacts.require("@openzeppelin/contracts/token/ERC20/IERC20.sol");
const MockERC20 = artifacts.require("MockUSDC");


contract("ChanclasICO", (accounts) => {
    const admin = accounts[0];
    const user = accounts[1];
    let chanclas, chanclasICO, usdcToken;

    before(async () => {
        console.log("Deploying MockERC20...");
        usdcToken = await MockERC20.new(web3.utils.toWei("100", "ether"), { from: user });
        console.log("MockERC20 deployed at:", usdcToken.address);

      
        console.log("Deploying Chanclas...");
        chanclas = await Chanclas.new("Chanclas", "CHNCLS", "http://localhost:3000/", admin, { from: admin });
        console.log("Chanclas deployed at:", chanclas.address);

        console.log("Preparing initial periods...");
        const initialPeriods = [
            [Math.floor(Date.now() / 1000) + 3600, 10, web3.utils.toWei("1", "ether"), 0],
            [Math.floor(Date.now() / 1000) + 7200, 20, web3.utils.toWei("1.5", "ether"), 0]
        ];

        console.log("Deploying ChanclasICO...");
        chanclasICO = await ChanclasICO.new(admin, usdcToken.address, chanclas.address, initialPeriods, { from: admin });
        console.log("ChanclasICO deployed at:", chanclasICO.address);

        console.log("Granting MINTER_ROLE to ChanclasICO...");
        const MINTER_ROLE = web3.utils.keccak256("MINTER_ROLE");
        await chanclas.grantRole(MINTER_ROLE, chanclasICO.address, { from: admin });
        console.log("MINTER_ROLE granted to ChanclasICO.");
    });

    it("should initialize with correct periods", async () => {
        const periods = await chanclasICO.periods(0); // Fetch first period
        assert.equal(periods.endTime > 0, true, "Period 0 should have a valid end time");
    });

    it("should apply discounted price after threshold", async () => {
        // First two mints at full price
        for (let i = 0; i < 2; i++) {
            await usdcToken.approve(chanclasICO.address, web3.utils.toWei("1", "ether"), { from: user });
            const tx = await chanclasICO.mint({ from: user });
            assert.equal(tx.logs[1].args.price.toString(), web3.utils.toWei("1", "ether"), 
                "First two mints should be full price");
        }

        // Third mint should get discount
        await usdcToken.approve(chanclasICO.address, web3.utils.toWei("0.65", "ether"), { from: user });
        const tx = await chanclasICO.mint({ from: user });
        assert.equal(tx.logs[1].args.price.toString(), web3.utils.toWei("0.65", "ether"), 
            "Third mint should get 35% discount");
    });

    
    it("should transition to the next period when max supply is reached", async () => {
        console.log("Minting all NFTs in the first period...");
    
        let expectedTokenId = 3;
    
        // Mint all NFTs for the first period
        for (let i = 0; i < 7; i++) {
            const period0Price = web3.utils.toWei("0.65", "ether");
            await usdcToken.approve(chanclasICO.address, period0Price, { from: user });
            const tx = await chanclasICO.mint({ from: user });
            const tokenId = tx.logs[0].args.tokenId.toNumber();
            const periodId = tx.logs[0].args.periodId.toNumber();
            //console.log(`Minted tokenId ${tokenId} in period ${periodId}`);
            assert.equal(periodId, 0, "Should mint in the first period");
            assert.equal(tokenId, expectedTokenId, `Token ID should be ${expectedTokenId}`);
            expectedTokenId++;
        }
    
        //console.log("Checking current period...");
        const currentPeriod = await chanclasICO.currentPeriodId();
        assert.equal(currentPeriod.toNumber(), 1, "Should transition to period 1");
    
        console.log("Minting all NFTs in the second period...");
        for (let i = 0; i < 20; i++) {
            const period1Price = web3.utils.toWei("0.975", "ether");
            await usdcToken.approve(chanclasICO.address, period1Price, { from: user });
            const tx = await chanclasICO.mint({ from: user });
            const tokenId = tx.logs[0].args.tokenId.toNumber();
            const periodId = tx.logs[0].args.periodId.toNumber();
            //console.log(`Minted tokenId ${tokenId} in period ${periodId}`);
            assert.equal(periodId, 1, "Should mint in the second period");
            assert.equal(tokenId, expectedTokenId, `Token ID should be ${expectedTokenId}`);
            expectedTokenId++;
        }
    
        console.log("Checking if periods are exhausted...");
        try {
            const period1Price = web3.utils.toWei("0.975", "ether");
            await usdcToken.approve(chanclasICO.address, period1Price, { from: user });
            await chanclasICO.mint({ from: user });
            assert.fail("Minting should fail after all periods are exhausted");
        } catch (error) {
            const errorMessage = error.message.toLowerCase();
            
            // Max supply reached for the current period
            assert.include(errorMessage, "current period max supply reached", "Should fail due to max supply");
            
        }
    });

    it("should allow admin to add new periods", async () => {
        const newPeriodEndTime = Math.floor(Date.now() / 1000) + 10800;
        const newPeriodMaxSupply = 15;
        const newPeriodPrice = web3.utils.toWei("2", "ether");

        await chanclasICO.addPeriod(
            newPeriodEndTime,
            newPeriodMaxSupply,
            newPeriodPrice,
            { from: admin }
        );

        const periods = await chanclasICO.getPeriods();
        assert.equal(periods.length, 3, "Should have 3 periods after addition");
        assert.equal(periods[2].maxSupply.toString(), newPeriodMaxSupply.toString(), 
            "New period max supply should match");
        const currentPeriodLastCheck = await chanclasICO.currentPeriodId();
        assert.equal(currentPeriodLastCheck.toString(), 2, "Should have 3 periods after addition");
    });
    
    

});