let currentImageIndex = 1;
const totalImages = 14; // Images from 0 to 10
const imgElement = document.getElementById("randomChanclas");

function changeImage() {
   
    setTimeout(() => {
        // Change the image source
        imgElement.src = `demo/${currentImageIndex}.png`;

        // Increment the index, reset if it exceeds totalImages
        currentImageIndex = (currentImageIndex + 1) % (totalImages + 1);

        
    }, 1000); // Wait for fade-out before changing image
}

// Initial call on page load
window.onload = () => {
    changeImage();
    setInterval(changeImage, 3000); // Change every 10 seconds
};