const fileInput = document.getElementById("file");
const filename = document.getElementById("filename");
const form = document.querySelector("form");
const loading = document.getElementById("loading");

fileInput.addEventListener("change", function () {

    if (this.files.length === 0) {
        filename.innerHTML = "📄 No file selected";
        return;
    }

    const file = this.files[0];

    // Check PDF
    if (file.type !== "application/pdf") {

        alert("❌ Please upload a PDF file only.");

        this.value = "";

        filename.innerHTML = "📄 No file selected";

        return;
    }

    // Maximum size 10 MB
    if (file.size > 10 * 1024 * 1024) {

        alert("❌ File size must be less than 10 MB.");

        this.value = "";

        filename.innerHTML = "📄 No file selected";

        return;
    }

    filename.innerHTML = "📄 " + file.name;

});

form.addEventListener("submit", function (e) {

    if (fileInput.files.length === 0) {

        e.preventDefault();

        alert("❌ Please choose a PDF first.");

        return;

    }

    loading.style.display = "block";

});