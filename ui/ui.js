window.process = { env: { NODE_ENV: "development" } };

let currentImageIndex = 1;
const totalImages = 14; // Images from 0 to 10
const imgElement = document.getElementById("randomChanclas");

import {
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
} from './web3.js';

let account;

let connectButtons = document.getElementsByClassName("open-connect-modal");

const navbar = document.getElementById("collapsibleNavbar");
// Add these selectors at the top
const mintControls = document.getElementById('mintControls');
const openMintBtn = document.querySelector('.open-mint-modal');
const approveBtn = document.getElementById('approveBtn');
const mintBtn = document.getElementById('mintBtn');
const mintAmount = document.getElementById('mintAmount');
const usdcBalanceSpan = document.getElementById('usdcBalance');
const usdcApprovedSpan = document.getElementById('usdcApproved');
const currentPriceSpan = document.getElementById('currentPrice');
const mintedAmountSpan = document.getElementById('mintedAmount');

function changeImage() {
   
    setTimeout(() => {
        // Change the image source
        imgElement.src = `demo/${currentImageIndex}.png`;

        // Increment the index, reset if it exceeds totalImages
        currentImageIndex = (currentImageIndex + 1) % (totalImages + 1);

        
    }, 1000); // Wait for fade-out before changing image
}


// Initialize the app and set up event listeners
window.addEventListener("load", async () => {
    changeImage();
    setInterval(changeImage, 3000); // Change every 10 seconds

    Array.from(connectButtons).forEach((btn) => {
      btn.addEventListener("click", () => {
        if (navbar && navbar.classList.contains("show")) {
          navbar.classList.remove("show");
      }
        openModal();
      });
    });
});

watchAccount(async (wagmiAccount) => {
    Array.from(connectButtons).forEach(async (btn) => {
      if (wagmiAccount.address && wagmiAccount.isConnected) {
        setAccount(wagmiAccount.address);
        account = wagmiAccount.address;

        // Show short address e.g. 0x12..3456
        const shortAddr = `${account.substring(0, 4)}...${account.substring(account.length - 4)}`;
        btn.textContent = shortAddr;
        await updateMintData();
      } else {
        setAccount(null);
        account = null;
        // Reset UI
        btn.textContent = "Connect Wallet";
        mintControls.style.display = 'none';
        openMintBtn.textContent = 'Red Envelop Mint';
      }
    });
  });

async function updateMintData() {
  if (!account) return;
  
  try {
    // Get USDC balance
    const balance = await readFromContract({
      address: usdcbase,
      abi: erc20Abi,
      functionName: 'balanceOf',
      args: [account]
    });
    usdcBalanceSpan.textContent = formatDecimalToUSD(balance);

    // Get USDC allowance
    const allowance = await readFromContract({
      address: usdcbase,
      abi: erc20Abi,
      functionName: 'allowance',
      args: [account, ico]
    });
    usdcApprovedSpan.textContent = formatDecimalToUSD(allowance);

    // Get current price
    const price = await readFromContract({
      address: ico,
      abi: ICOAbi,
      functionName: 'getCurrentRebate',
      account: account, // ⚡️ Critical: Pass the user's address
    });
   
    currentPriceSpan.textContent = formatDecimalToUSD(price);

    // // Get minted amount
    // const minted = await readFromContract({
    //   address: ico,
    //   abi: ICOAbi,
    //   functionName: 'mintedPerUser',
    //   args: [account]
    // });
    // mintedAmountSpan.textContent = formatNumberWithCommas(minted);

  } catch (error) {
    console.error('Error updating mint data:', error);
  }
}

// Toggle mint controls
openMintBtn.addEventListener('click', async () => {
  if (!account) {
    openModal();
    return;
  }
  
  if (mintControls.style.display === 'none') {
    mintControls.style.display = 'block';
    openMintBtn.textContent = 'Hide Mint Interface';
    await updateMintData();
  } else {
    mintControls.style.display = 'none';
    openMintBtn.textContent = 'Red Envelop Mint';
  }
});

// Approval handler
approveBtn.addEventListener('click', async () => {
  const amount = BigInt(mintAmount.value * 1e6); // USDC has 6 decimals
  
  try {
    const { hash } = await writeToContract({
      address: usdcbase,
      abi: erc20Abi,
      functionName: 'approve',
      args: [ico, amount],
      account
    });
    await updateMintData();
  } catch (error) {
    console.error('Approval failed:', error);
  }
});

// Function to query backend after minting
async function queryBackendAfterMint(tokenId) {
  try {
    console.log(`Querying backend for token ${tokenId}...`);
    
    // Query the metadata endpoint to trigger generation and OpenSea refresh
    const response = await fetch(`${backend_api}id/${tokenId}`);
    
    if (response.ok) {
      const metadata = await response.json();
      console.log(`Successfully generated metadata for token ${tokenId}:`, metadata);
    } else {
      console.error(`Backend query failed for token ${tokenId}:`, response.status, response.statusText);
    }
  } catch (error) {
    console.error(`Error querying backend for token ${tokenId}:`, error);
  }
}

// Mint handler
mintBtn.addEventListener('click', async () => {
  
  try {
    const { hash: txHash, receipt } = await writeToContract({
      address: ico,
      abi: ICOAbi,
      functionName: 'mint',
      args: [],
      account
    });
    
    console.log('Mint transaction hash:', txHash);
    
    // Extract token ID from transaction receipt using wagmi infrastructure
    try {
      const tokenId = await extractTokenIdFromMintTransaction(receipt);
      
      // Query backend to generate metadata and trigger OpenSea refresh
      await queryBackendAfterMint(tokenId);
      
    } catch (extractError) {
      console.error('Failed to extract token ID or query backend:', extractError);
      // Continue with normal flow even if backend query fails
    }
    
    await updateMintData();
  } catch (error) {
    console.error('Minting failed:', error);
  }
});

