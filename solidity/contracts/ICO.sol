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
        address nftContractAddress
    ) {
        admin = _admin;
        _grantRole(DEFAULT_ADMIN_ROLE, _admin);

        usdc = IERC20(usdcAddress);
        nftContract = Chanclas(nftContractAddress);

        periods.push(Period({
            endTime: block.timestamp + 10 days,
            maxSupply: 1000,
            price: 1500000,
            mintedCount: 32
        }));

        require(periods.length > 0, "At least one period must be defined");
        
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
        // Check if we need to advance the period due to time expiry
        updatePeriodIfExpired();
        
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

    // Helper function to update the current period if it has expired
    function updatePeriodIfExpired() public {
        while (currentPeriodId < periods.length) {
            Period storage period = periods[currentPeriodId];
            
            // If current period is not expired, we're done
            if (block.timestamp <= period.endTime) {
                break;
            }
            
            // If there's a next period, advance to it
            if (currentPeriodId + 1 < periods.length) {
                currentPeriodId++;
            } else {
                // We're at the last period, even if expired
                break;
            }
        }
    }

    function getCurrentRebate() external view returns (uint256) {
        uint256 localCurrentPeriod = currentPeriodId;
        
        // Ensure we have a valid period
        require(localCurrentPeriod < periods.length, "No active periods");
        
        uint256 userMints = mintedPerUser[msg.sender][localCurrentPeriod];
        uint256 extraMints = userMints + 1; // Start counting from first mint
        uint256 discount = (maxRebate * extraMints) / (extraMints + curveSteepness);

        uint256 pricePerNFT = periods[localCurrentPeriod].price * (100 - discount) / 100;
        return pricePerNFT;
    }


    function getCurrentPeriod() external view returns (uint256 periodId, Period memory period) {
        require(periods.length > 0, "No periods defined");
        
        // Create a local copy of currentPeriodId for view function simulation
        uint256 localCurrentPeriod = currentPeriodId;
        
        // Simulate updatePeriodIfExpired logic for view function
        while (localCurrentPeriod < periods.length) {
            Period memory activePeriod = periods[localCurrentPeriod];
            
            if (block.timestamp <= activePeriod.endTime) {
                break;
            }
            
            if (localCurrentPeriod + 1 < periods.length) {
                localCurrentPeriod++;
            } else {
                // We're at the last period, even if expired
                break;
            }
        }
        
        // Make sure we haven't gone beyond the last period
        require(localCurrentPeriod < periods.length, "No active periods");
        
        return (localCurrentPeriod, periods[localCurrentPeriod]);
    }

    function getPeriods() external view returns (Period[] memory) {
        return periods;
    }
}