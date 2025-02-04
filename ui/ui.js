window.process = { env: { NODE_ENV: "development" } };

let currentImageIndex = 1;
const totalImages = 14; // Images from 0 to 10
const imgElement = document.getElementById("randomChanclas");

import {
  openModal,
  watchAccount,
  setAccount,
  getAccount,
  signNonce,
  formatNumberWithCommas,
  formatWeiToEth,
  backend_api,
} from './web3.js';

let account;

let connectButtons = document.getElementsByClassName("open-connect-modal");


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
      } else {
        setAccount(null);
        account = null;
        // Reset UI
        btn.textContent = "Connect Wallet";
      }
    });
  });