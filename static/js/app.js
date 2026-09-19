document.addEventListener("DOMContentLoaded", () => {

    console.log("CivicShield initialized successfully.");

    const locationButton =
        document.getElementById("location-button");

    const locationStatus =
        document.getElementById("location-status");

    const latitudeInput =
        document.getElementById("id_latitude");

    const longitudeInput =
        document.getElementById("id_longitude");

    const locationInput =
        document.getElementById("id_location");


    if (locationButton) {

        locationButton.addEventListener("click", () => {

            if (!navigator.geolocation) {

                locationStatus.textContent =
                    "❌ Geolocation is not supported by your browser.";

                return;
            }


            locationButton.disabled = true;

            locationButton.textContent =
                "📍 Detecting location...";


            navigator.geolocation.getCurrentPosition(

                (position) => {

                    const latitude =
                        position.coords.latitude;

                    const longitude =
                        position.coords.longitude;


                    latitudeInput.value = latitude;

                    longitudeInput.value = longitude;


                    locationInput.value =
                        `Latitude: ${latitude.toFixed(6)}, Longitude: ${longitude.toFixed(6)}`;


                    locationStatus.textContent =
                        "✅ Location detected successfully.";


                    locationButton.textContent =
                        "📍 Location Detected";


                    locationButton.disabled = false;

                },

                (error) => {

                    console.error(error);


                    locationStatus.textContent =
                        "❌ Unable to detect location. Please enter it manually.";


                    locationButton.textContent =
                        "📍 Try Again";


                    locationButton.disabled = false;

                }

            );

        });

    }

});