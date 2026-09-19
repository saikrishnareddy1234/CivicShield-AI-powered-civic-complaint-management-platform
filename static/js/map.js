document.addEventListener("DOMContentLoaded", () => {

    const map = L.map("civic-map").setView(
        [17.3850, 78.4867],
        12
    );


    L.tileLayer(
    "https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png",
    {
        attribution:
            '&copy; OpenStreetMap contributors &copy; CARTO',
        subdomains: "abcd",
        maxZoom: 20
    }
).addTo(map);


    fetch("/api/complaints/")
        .then(response => response.json())
        .then(data => {

            const complaints = data.complaints;

            let highCount = 0;
            let resolvedCount = 0;


            document.getElementById(
                "total-count"
            ).textContent = complaints.length;


            complaints.forEach(complaint => {

                if (complaint.priority === "high") {
                    highCount++;
                }

                if (complaint.status === "resolved") {
                    resolvedCount++;
                }


                let markerColor = "#3b82f6";


                if (
                    complaint.priority === "high" ||
                    complaint.priority === "critical"
                ) {

                    markerColor = "#ef4444";

                } else if (
                    complaint.priority === "medium"
                ) {

                    markerColor = "#f59e0b";

                } else if (
                    complaint.status === "resolved"
                ) {

                    markerColor = "#22c55e";

                }


                const marker = L.circleMarker(
                    [
                        complaint.latitude,
                        complaint.longitude
                    ],
                    {
                        radius: 9,
                        fillColor: markerColor,
                        color: "#ffffff",
                        weight: 2,
                        opacity: 1,
                        fillOpacity: 0.8
                    }
                );


                marker.bindPopup(`
                    <div style="min-width:220px">

                        <h3>
                            ${complaint.category}
                        </h3>

                        <p>
                            ${complaint.description}
                        </p>

                        <hr>

                        <strong>
                            Priority:
                        </strong>
                        ${complaint.priority}

                        <br>

                        <strong>
                            Status:
                        </strong>
                        ${complaint.status}

                        <br>

                        <strong>
                            Department:
                        </strong>
                        ${complaint.department || "Not assigned"}

                        <br><br>

                        <small>
                            ${complaint.created_at}
                        </small>

                    </div>
                `);


                marker.addTo(map);

            });


            document.getElementById(
                "high-count"
            ).textContent = highCount;


            document.getElementById(
                "resolved-count"
            ).textContent = resolvedCount;

        })

        .catch(error => {

            console.error(
                "Unable to load complaints:",
                error
            );

        });

});