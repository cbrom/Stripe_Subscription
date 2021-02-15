// static/main.js

console.log("Sanity check!");

// Get Stripe publishable key
fetch("/subscriptions/config/")
.then((result) => { return result.json(); })
.then((data) => {
  // Initialize Stripe.js
  const stripe = Stripe(data.publicKey);

  // Event handler
  let subButton = document.querySelector("#subButton");
  if (subButton !== null) {
    subButton.addEventListener("click", () => {
    // Get Checkout Session ID
    fetch("/subscriptions/create-checkout-session/")
      .then((result) => { return result.json(); })
      .then((data) => {
        console.log("****", data);
        // Redirect to Stripe Checkout
        return stripe.redirectToCheckout({sessionId: data.sessionId})
      })
      .then((res) => {
        console.log(res);
      });
    });
  }

  let cancButton = document.querySelector("#cancButton");
  if (cancButton !== null) {
    cancButton.addEventListener("click", () => {
    // Get Checkout Session ID
    fetch("cancel_subscription/", {method: 'POST'})
      .then((result) => { 
          if (result.status == 200) {
            window.location.reload();
          }
      });
    });
  }


});