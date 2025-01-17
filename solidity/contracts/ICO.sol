// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "../node_modules/openzeppelin/contracts/access/AccessControl.sol";
import "../node_modules/openzeppelin/contracts/token/ERC20/IERC20.sol";
import "./Chanclas.sol";

contract ChanclasICO is AccessControl {
    
    address public admin;

    struct Period {
        uint256 endTime;      // End time of the period
        uint256 maxSupply;    // Maximum supply for this period
        uint256 price;        // Price per NFT in USDC
        uint256 mintedCount;  // Number of NFTs minted in this period
    }

    uint256 public currentPeriodId;  // Index of the current period
    Period[] public periods;         // Array of all periods

    IERC20 public usdc;              // USDC token contract
    Chanclas public nftContract;     // Chanclas NFT contract

    event Minted(address indexed buyer, uint256 indexed tokenId, uint256 periodId, uint256 price);

    constructor(
        address _admin,
        address usdcAddress,
        address nftContractAddress,
        Period[] memory initialPeriods
    ) {
        _grantRole(DEFAULT_ADMIN_ROLE, admin);

        admin = _admin;

        usdc = IERC20(usdcAddress);
        nftContract = Chanclas(nftContractAddress);

        // Initialize periods
        for (uint256 i = 0; i < initialPeriods.length; i++) {
            periods.push(initialPeriods[i]);
        }

        // Set the first period as the active one
        require(periods.length > 0, "At least one period must be defined");
        currentPeriodId = 0;
    }

    function mint() external {
        // Lock the current period
        Period storage period = periods[currentPeriodId];

        // Ensure the current period is valid
        require(block.timestamp <= period.endTime, "Current period has ended");
        require(period.mintedCount < period.maxSupply, "Current period max supply reached");
        

        // Transfer USDC from the buyer to the admin
        uint256 price = period.price;
        require(usdc.transferFrom(msg.sender, admin, price), "USDC transfer failed");

        // Mint the NFT
        nftContract.mint(msg.sender, currentPeriodId);

        // Update the period's minted count
        period.mintedCount++;

         // Transition to the next period if this mint exhausts the current period
        if (period.mintedCount == period.maxSupply) {
            if (currentPeriodId + 1 < periods.length) {
                currentPeriodId++;
            }
        }

        

        // Emit Minted event
        emit Minted(msg.sender, nftContract.currentTokenId() - 1, currentPeriodId, price);

       
    }





    function getCurrentPeriod() external view returns (uint256 periodId, Period memory period) {
        // Return the current active period
        require(currentPeriodId < periods.length, "No active periods");
        Period memory activePeriod = periods[currentPeriodId];

        // Check if the current period is still active
        if (block.timestamp <= activePeriod.endTime && activePeriod.mintedCount < activePeriod.maxSupply) {
            return (currentPeriodId, activePeriod);
        }

        // Check if there's a next period
        if (currentPeriodId + 1 < periods.length) {
            return (currentPeriodId + 1, periods[currentPeriodId + 1]);
        }

        revert("No active periods");
    }

    function getPeriods() external view returns (Period[] memory) {
        return periods;
    }
}
