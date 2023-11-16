async function injectHTML(filePath, elem) {
    try {
        const response = await fetch(filePath);
        if (!response.ok) {
            return;
        }
        const text = await response.text();
        elem.innerHTML = text;
    } catch (err) {
        console.error(err.message);
    }
}

async function main() {

    await injectHTML("../modules/navbar.html",
        document.querySelector(".navigation")
    );
    var actives = document.querySelectorAll(".activeToggle");
    for (let i = 0; i < actives.length; i++) {
        if (actives[i].hasAttribute("id") && window.location.pathname.includes(actives[i].id)) {
            actives[i].classList.add("active");
        }
    }

    await injectHTML("../modules/footer.html",
        document.querySelector(".footer")
    );
}

main();