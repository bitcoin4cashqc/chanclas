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
const chanclas721 = "0x73e88cfC79be97f8FB706Aa8476066C87eEa4Fc0";

const backend_api = "https://chanclas.fun/";

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
async function readFromContract({ address, abi, functionName, args = [] }) {
  return await readContract({ address, abi, functionName, args });
}

async function writeToContract({ address, abi, functionName, args = [], account }) {
  const { hash } = await writeContract({ address, abi, functionName, args, account });
  await waitForTransaction({ hash });
  return hash;
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
  signNonce,
  backend_api,
  formatWeiToEth,
  formatNumberWithCommas
};
