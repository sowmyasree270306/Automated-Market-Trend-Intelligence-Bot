function showSection(sectionId) {

    let sections = document.querySelectorAll(".content-section");

    sections.forEach(section => {
        section.style.display = "none";
    });

    document.getElementById(sectionId).style.display = "block";
}

window.onload = function () {
    showSection("overview");
}