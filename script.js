// Get the image container and the first image
const imageContainer = document.getElementById("image-wrapper");
const moveContainer = document.getElementById("move-wrapper");
const container = document.getElementById("container");
const minimumScaleFactor = 0.3; // Adjust this value as needed

// Get the hidden input field for storing the scale factor
const scaleFactorInput = document.getElementById("scaleFactorInput");

// Function to apply the scale factor to all images
function applyScaleToImages() {
  const images = imageContainer.querySelectorAll("img");
  images.forEach((img) => {
    img.style.transform = `translate(-50%, -50%) scale(${scaleFactorInput.value})`;
  });
}

// Check if there is a saved scale factor in local storage
let scaleFactor = parseFloat(localStorage.getItem("zoomScale")) || 1.0;
scaleFactorInput.value = scaleFactor; // Set the initial value of the hidden input

// Add an event listener for the mousewheel event on the container
imageContainer.addEventListener("wheel", (event) => {
  // Calculate the new scale factor based on scroll direction
  if (event.deltaY > 0) {
    scaleFactor = Math.max(scaleFactor - 0.1, minimumScaleFactor); // Decrease scale on scroll down
  } else {
    scaleFactor += 0.1; // Increase scale on scroll up
  }

  // Update the hidden input field with the new scale factor
  scaleFactorInput.value = scaleFactor;

  // Apply the scale factor to all images
  applyScaleToImages();

  // Save the current scale factor to local storage
  localStorage.setItem("zoomScale", scaleFactor.toString());
});

// Variables to track the mouse position and dragging state
let isDragging = false;
let initialMouseX;
let initialMouseY;
let initialImageX;
let initialImageY;

// Variables to store the current offset due to mouse movement
let mouseMovementX = 0;
let mouseMovementY = 0;

// Function to handle the mouse down event
function onMouseDown(event) {
  isDragging = true;
  initialMouseX = event.clientX;
  initialMouseY = event.clientY;
  // Initialize mouse movement offsets with the current position
  mouseMovementX = 0;
  mouseMovementY = 0;

  // Add "grabbing" cursor style
  moveContainer.style.cursor = "grabbing";
}

// Function to handle the mouse move event
function onMouseMove(event) {
   if (!isDragging) return;

  const deltaX = event.clientX - initialMouseX;
  const deltaY = event.clientY - initialMouseY;

  // Apply the new position to each image separately while preserving their existing offset
  const images = imageContainer.querySelectorAll("img");
  images.forEach((img) => {
    const imgLeft = img.style.left;
    const imgTop = img.style.top;
    console.log(imgLeft + " " + imgTop)
    const newLeft = `calc(${imgLeft} + ${deltaX}px)`;
    const newTop = `calc(${imgTop} + ${deltaY}px)`;
    img.style.left = `${newLeft}`;
    img.style.top = `${newTop}`;
  });

  // Update the initial mouse position
  initialMouseX = event.clientX;
  initialMouseY = event.clientY;
}

// Function to handle the mouse up event
function onMouseUp() {
  isDragging = false;
  // Restore the default cursor style
  moveContainer.style.cursor = "grab";
}

// Function to prevent the default drag behavior
function preventDefaultDrag(event) {
  event.preventDefault();
}

// Add event listeners for mouse events on the move-container
document.addEventListener("mousedown", onMouseDown);
document.addEventListener("mousemove", onMouseMove);
document.addEventListener("mouseup", onMouseUp);

// Add an event listener to prevent default drag behavior on the move-container
moveContainer.addEventListener("dragstart", preventDefaultDrag);
