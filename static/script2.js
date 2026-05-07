// toggle CA details
    function toggleDetails(el) {
        const box = el.nextElementSibling;

        if (box.style.display === "block") {
            box.style.display = "none";
            el.innerText = "Show Details";
        } else {
            box.style.display = "block";
            el.innerText = "Hide Details";
        }
    }

    // search filter
    function searchTable() {
        const input = document.getElementById("searchInput").value.toLowerCase();
        const rows = document.querySelectorAll("#certTable tbody tr");

        rows.forEach(row => {
            const domain = row.children[0].innerText.toLowerCase();

            if (domain.includes(input)) {
                row.style.display = "";
            } else {
                row.style.display = "none";
            }
        });
    }