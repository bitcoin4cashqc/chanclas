// scripts/wagmiConfig.js
import {
  EthereumClient,
  w3mConnectors,
  w3mProvider,
  WagmiCore,
} from 'https://unpkg.com/@web3modal/ethereum@2.7.1';
import { Web3Modal } from 'https://unpkg.com/@web3modal/html@2.7.1';
import { chains } from './chains.js';


const {
  readContract,
  writeContract,
  waitForTransaction,
  configureChains,
  createConfig,
  signMessage,
} = WagmiCore;

// Example project ID from Web3Modal
const projectId = '4a2aad5472b76afb2a498c7c9bb03197';

// Example addresses
const chanclas721 = "0x262cA2E567315300CDdf389A0D2E37212F4DAEF4";
const ico = "0xa1D824Fff9572BaEe4e970b99A8527887440832F"
const usdcbase = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"

const backend_api = "https://chanclas.fun/";

import { erc20Abi } from './erc20abi.js';
import { ChanclasAbi } from './Chanclasabi.js';
import { ICOAbi } from './ICOAbi.js';


let account = null;

// Configure WAGMI + Web3Modal
const { publicClient } = configureChains(chains, [w3mProvider({ projectId })]);
const wagmiConfig = createConfig({
  autoConnect: true,
  connectors: w3mConnectors({ projectId, chains }),
  publicClient,
});
const ethereumClient = new EthereumClient(wagmiConfig, chains);
const web3modal = new Web3Modal({ projectId }, ethereumClient);



/** Contract read/write */
async function readFromContract({ address, abi, functionName, args = [], account = null}) {
  let data;
  if (account == null) {
    data = { address, abi, functionName, args}
  }else{
    data = { address, abi, functionName, args, account}
  }
  
  return await readContract(data);
}

async function writeToContract({ address, abi, functionName, args = [], account }) {
  const { hash } = await writeContract({ address, abi, functionName, args, account });
  const receipt = await waitForTransaction({ hash });
  return { hash, receipt };
}

/** Extract token ID from mint transaction receipt */
async function extractTokenIdFromMintTransaction(receipt) {
  try {
    console.log('Parsing transaction receipt for logs:', receipt);
    
    if (!receipt || !receipt.logs) {
      throw new Error('No logs found in transaction receipt');
    }
    
    console.log('Transaction receipt logs:', receipt.logs);
    
    // Look for the Minted event
    // The Minted event has signature: Minted(address indexed buyer, uint256 indexed tokenId, uint256 periodId, uint256 price)
    // The topic for Minted event (keccak256 of the event signature)
    const mintedEventTopic = '0x5a3358a3d27a5373c0df2604662088d37894d56b7cfd27f315770440f4e0d919';
    
    for (const log of receipt.logs) {
      if (log.topics && log.topics[0] === mintedEventTopic) {
        // tokenId is the second indexed parameter (topics[2])
        const tokenId = parseInt(log.topics[2], 16);
        console.log(`Found minted token ID: ${tokenId}`);
        return tokenId;
      }
    }
    
    throw new Error('Minted event not found in transaction logs');
  } catch (error) {
    console.error('Error extracting token ID from transaction:', error);
    throw error;
  }
}

/**
 * Converts Wei (BigInt or string) to Ether as a human-readable string.
 * @param {BigInt|string} wei - The amount in Wei.
 * @returns {string} - The equivalent value in Ether.
 */
function formatWeiToEth(wei) {
  const weiBigInt = BigInt(wei); // Ensure it's a BigInt
  const ether = (weiBigInt / BigInt(1e18)).toString(); // Convert to Ether
  return ether;
}

/**
 * Converts Wei (BigInt or string) to Ether as a human-readable string.
 * @param {BigInt|string} wei - The amount in Wei.
 * @returns {string} - The equivalent value in Ether.
 */
function formatDecimalToUSD(amount) {
  
  const usdcUnits = BigInt(amount);
  const divisor = BigInt(1e6); // USDC has 6 decimals

  const integerPart = usdcUnits / divisor;
  const remainder = usdcUnits % divisor;

  if (remainder === 0n) {
    return integerPart.toString();
  }

  // Pad remainder to 6 digits and trim trailing zeros
  const remainderStr = remainder.toString().padStart(6, '0').replace(/0+$/, '');
  return `${integerPart.toString()}.${remainderStr}`;
}


/**
 * Formats a number with commas for better readability.
 * @param {string|number} number - The number to format.
 * @returns {string} - The formatted number with commas.
 */
function formatNumberWithCommas(number) {
  const numString = number.toString(); // Ensure it's a string
  return numString.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}


/** sign a nonce with Wagmi's signMessage */
async function signNonce(nonce) {
  const signRes = await signMessage({ message: nonce });
  if (signRes.error) {
    throw new Error("Could not sign message: " + signRes.error.message);
  }
  return signRes.data || signRes;
}

/** open the Web3Modal */
function openModal() {
  web3modal.openModal();
}

/** watchAccount => run a callback whenever the connected account changes */
function watchAccount(callback) {
  ethereumClient.watchAccount((wagmiAccount) => {
    callback(wagmiAccount);
  });
}

function setAccount(addr) {
  account = addr;
}
function getAccount() {
  return account;
}


export {
  web3modal,
  openModal,
  watchAccount,
  setAccount,
  getAccount,
  readFromContract,
  writeToContract,
  extractTokenIdFromMintTransaction,
  signNonce,
  backend_api,
  formatWeiToEth,
  formatNumberWithCommas,
  erc20Abi,
  ChanclasAbi,
  ICOAbi,
  usdcbase,
  chanclas721,
  ico,
  formatDecimalToUSD,
};
