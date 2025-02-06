// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "../node_modules/openzeppelin/contracts/access/AccessControl.sol";
import "../node_modules/openzeppelin/contracts/token/ERC20/IERC20.sol";
import "./Chanclas.sol";

contract ChanclasICO is AccessControl {
    address public admin;
   
    struct Period {
        uint256 endTime;
        uint256 maxSupply;
        uint256 price;
        uint256 mintedCount;
    }

    uint256 public currentPeriodId;
    Period[] public periods;
    IERC20 public usdc;
    Chanclas public nftContract;
    
    mapping(address => mapping(uint256 => uint256)) public mintedPerUser;
    uint16 public maxRebate = 50;
    uint16 public curveSteepness = 1;

    event Minted(address indexed buyer, uint256 indexed tokenId, uint256 periodId, uint256 price);
    event PeriodAdded(uint256 periodId, uint256 endTime, uint256 maxSupply, uint256 price);

    constructor(
        address _admin,
        address usdcAddress,
        address nftContractAddress,
        Period[] memory initialPeriods
    ) {
        admin = _admin;
        _grantRole(DEFAULT_ADMIN_ROLE, _admin);

        usdc = IERC20(usdcAddress);
        nftContract = Chanclas(nftContractAddress);

        for (uint256 i = 0; i < initialPeriods.length; i++) {
            periods.push(initialPeriods[i]);
        }

        require(periods.length > 0, "At least one period must be defined");
        currentPeriodId = 0;
    }

    function changeBonus(uint16 _maxRebate, uint16 _curveSteepness) external  onlyRole(DEFAULT_ADMIN_ROLE){
        maxRebate = _maxRebate;
        curveSteepness = _curveSteepness;
    }

    function addPeriod(
        uint256 endTime,
        uint256 maxSupply,
        uint256 price
    ) external onlyRole(DEFAULT_ADMIN_ROLE) {
        
        periods.push(Period({
            endTime: endTime,
            maxSupply: maxSupply,
            price: price,
            mintedCount: 0
        }));
        Period storage period = periods[currentPeriodId];
        if (period.mintedCount == period.maxSupply) {
            currentPeriodId++;
        }
        
        emit PeriodAdded(periods.length - 1, endTime, maxSupply, price);
    }

    function mint() external {
        Period storage period = periods[currentPeriodId];
        require(block.timestamp <= period.endTime, "Current period has ended");
        require(period.mintedCount < period.maxSupply, "Current period max supply reached");

        uint256 userMints = mintedPerUser[msg.sender][currentPeriodId];
        uint256 extraMints = userMints + 1; // Start counting from first mint
        uint256 discount = (maxRebate * extraMints) / (extraMints + curveSteepness);

        uint256 pricePerNFT = period.price * (100 - discount) / 100;

        require(usdc.transferFrom(msg.sender, admin, pricePerNFT), "USDC transfer failed");

        nftContract.mint(msg.sender,currentPeriodId,extraMints,curveSteepness,maxRebate);
        period.mintedCount++;
        mintedPerUser[msg.sender][currentPeriodId]++;


        emit Minted(msg.sender, nftContract.currentTokenId() - 1, currentPeriodId, pricePerNFT);
        if (period.mintedCount == period.maxSupply && currentPeriodId + 1 < periods.length) {
            currentPeriodId++;
        }
    }

    function getCurrentRebate() external view returns (uint256) {
        Period storage period = periods[currentPeriodId];

        uint256 userMints = mintedPerUser[msg.sender][currentPeriodId];
        uint256 extraMints = userMints + 1; // Start counting from first mint
        uint256 discount = (maxRebate * extraMints) / (extraMints + curveSteepness);

        uint256 pricePerNFT = period.price * (100 - discount) / 100;
        return pricePerNFT;

    }


    function getCurrentPeriod() external view returns (uint256 periodId, Period memory period) {
        require(currentPeriodId < periods.length, "No active periods");
        Period memory activePeriod = periods[currentPeriodId];

        if (block.timestamp <= activePeriod.endTime && activePeriod.mintedCount < activePeriod.maxSupply) {
            return (currentPeriodId, activePeriod);
        }

        if (currentPeriodId + 1 < periods.length) {
            return (currentPeriodId + 1, periods[currentPeriodId + 1]);
        }

        revert("No active periods");
    }

    function getPeriods() external view returns (Period[] memory) {
        return periods;
    }
}