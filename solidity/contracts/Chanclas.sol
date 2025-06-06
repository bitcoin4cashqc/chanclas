// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "../node_modules/openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "../node_modules/openzeppelin/contracts/token/ERC721/ERC721.sol";
import "../node_modules/openzeppelin/contracts/access/AccessControl.sol";

contract Chanclas is ERC721, AccessControl {
    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");
    uint256 public currentTokenId;
    string private baseTokenURI;

    // Struct to hold additional data for tokens
    struct TokenData {
        uint256 seed;
        uint256 periodId;
        uint256 extraMints;
        uint16 curveSteepness;
        uint16 maxRebate;
    }

    // Mapping from tokenId to TokenData
    mapping(uint256 => TokenData) private tokenData;

    constructor(string memory name, string memory symbol, string memory initialBaseURI) ERC721(name, symbol) {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender); // Grant admin role to contract deployer
        baseTokenURI = initialBaseURI; // Set initial base URI
    }

    // Mint function with `periodId`
    function mint(address to, uint256 periodId,uint256 extraMints,uint16 curveSteepness,uint16 maxRebate) external onlyRole(MINTER_ROLE) {
        
        uint256 tokenId = currentTokenId;

        // Generate a unique seed using block.timestamp, periodId, and tokenId
        uint256 seed = uint256(keccak256(abi.encodePacked(block.timestamp, periodId, tokenId, extraMints, curveSteepness, maxRebate)));

        // Store token data
        tokenData[tokenId] = TokenData({ seed: seed, periodId: periodId, extraMints: extraMints, curveSteepness: curveSteepness, maxRebate: maxRebate});

        // Mint the token to the specified address
        _mint(to, tokenId);

        currentTokenId++;

        // Emit an event for tracking
        emit Minted(to, tokenId, periodId, seed);
    }

    // Get token data (periodId and seed)
    function getTokenData(uint256 tokenId) external view returns (uint256 seed, uint256 periodId,uint256 extraMints,uint16 curveSteepness,uint16 maxRebate) {
        TokenData memory data = tokenData[tokenId];
        return (data.seed, data.periodId,data.extraMints,data.curveSteepness,data.maxRebate);
    }

    // Set base token URI (only admin can set this)
    function setBaseTokenURI(string memory newBaseTokenURI) external onlyRole(DEFAULT_ADMIN_ROLE) {
        baseTokenURI = newBaseTokenURI;
    }

    // Override _baseURI to return the baseTokenURI
    function _baseURI() internal view override returns (string memory) {
        return baseTokenURI;
    }



    // Override supportsInterface to resolve conflict between ERC721 and AccessControl
    function supportsInterface(bytes4 interfaceId) public view override(ERC721, AccessControl) returns (bool) {
        return super.supportsInterface(interfaceId);
    }

    // Event emitted on minting
    event Minted(address indexed to, uint256 indexed tokenId, uint256 periodId, uint256 seed);
}
