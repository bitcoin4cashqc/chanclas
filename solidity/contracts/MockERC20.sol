// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
import "../node_modules/openzeppelin/contracts/token/ERC20/ERC20.sol";

contract MockUSDC is ERC20 {
    constructor(uint256 initialSupply) ERC20("Fake USDC", "USDC") {
        _mint(msg.sender, initialSupply);
    }
}