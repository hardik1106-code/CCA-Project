function handleSearch(event) {
    event.preventDefault(); // stop normal form submit

    let query = document.getElementById("searchBox").value.toLowerCase();

    if (query === "gov.in") {
        window.location.href = "http://127.0.0.1:8000/gov.in";
    } else {
        window.location.href = "results.html?query=" + encodeURIComponent(query);
    }
}