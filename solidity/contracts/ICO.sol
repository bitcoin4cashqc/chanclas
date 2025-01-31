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
    
    mapping(address => uint256) public mintedPerUser;
    uint16 public bonusMintedCount = 2;
    uint16 public bonusMintedPercent = 65;

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

    function changeBonus(uint16 _bonusMintedCount, uint16 _bonusMintedPercent) external  onlyRole(DEFAULT_ADMIN_ROLE){
        bonusMintedCount = _bonusMintedCount;
        bonusMintedPercent = _bonusMintedPercent;
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

        uint256 pricePerNFT = period.price;
        if (mintedPerUser[msg.sender] >= bonusMintedCount) {
            pricePerNFT = (pricePerNFT * bonusMintedPercent) / 100;
        }

        require(usdc.transferFrom(msg.sender, admin, pricePerNFT), "USDC transfer failed");

        nftContract.mint(msg.sender, currentPeriodId);
        period.mintedCount++;
        mintedPerUser[msg.sender]++;

        if (period.mintedCount == period.maxSupply && currentPeriodId + 1 < periods.length) {
            currentPeriodId++;
        }

        emit Minted(msg.sender, nftContract.currentTokenId() - 1, currentPeriodId, pricePerNFT);
    }

    // Existing view functions remain the same
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