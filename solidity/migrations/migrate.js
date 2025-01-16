const Chanclas = artifacts.require("Chanclas");
const ChanclasICO = artifacts.require("ChanclasICO");
const IERC20 = artifacts.require("@openzeppelin/contracts/token/ERC20/IERC20.sol");

module.exports = async function (deployer, network, accounts) {
    const admin = accounts[0]; // Deployer account as admin
    const icoMinter = accounts[1]; // ICO minter role
    const usdcToken = accounts[2]; // Mock USDC address (use a deployed ERC20 for testing)
    const baseURI = "http://localhost:3000/";

    // Define initial periods
    const initialPeriods = [
        { endTime: Math.floor(Date.now() / 1000) + 3600, maxSupply: 10, price: web3.utils.toWei("1", "ether") }, // 1 hour
        { endTime: Math.floor(Date.now() / 1000) + 7200, maxSupply: 20, price: web3.utils.toWei("1.5", "ether") } // 2 hours
    ];

    // Deploy Chanclas NFT contract
    await deployer.deploy(Chanclas, "Chanclas", "CHNCLS", baseURI, icoMinter);
    const chanclas = await Chanclas.deployed();

    console.log("Chanclas deployed at:", chanclas.address);

    // Deploy ChanclasICO contract
    await deployer.deploy(ChanclasICO, admin, usdcToken, chanclas.address, initialPeriods);
    const chanclasICO = await ChanclasICO.deployed();

    console.log("ChanclasICO deployed at:", chanclasICO.address);

    // Grant MINTER_ROLE to ChanclasICO
    const MINTER_ROLE = web3.utils.keccak256("MINTER_ROLE");
    await chanclas.grantRole(MINTER_ROLE, chanclasICO.address);
    console.log("Granted MINTER_ROLE to ChanclasICO:", chanclasICO.address);
};
