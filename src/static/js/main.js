let current_theme = "";

function resetAllThemes(){
    document.body.classList.forEach(cls => {
    if (cls.startsWith('theme-')) {
        document.body.classList.remove(cls);
    }});
}

function setNewTheme(newTheme) {
    if (newTheme === current_theme) {
        return;
    }
    resetAllThemes();
    document.body.classList.toggle(newTheme);
    current_theme = newTheme;
}

async function longUpdate() {
    const date = new Date();
    const hour = date.getHours();
    const month = date.getMonth() + 1;
    const day = date.getDate();
    const isDay = (hour > 9 && hour < 18);

    let is_golden = true;
    let bgImage = "url(../static/img/darkmodeF.png)";
    

    if (month === 2 && [12, 13, 14].includes(day)) {
        bgImage = "url(../static/img/valentinemode.png)";
    } else if (month === 3 && day === 13) {
        bgImage = "url(../static/img/jumpstartbang.png)";
    } else if (month === 4 && [10, 11, 12].includes(day)) {
        is_golden = true;
    } else if (month === 10 && [29, 30, 31].includes(day)) {
        bgImage = "url(../static/img/spookymode.png)";
    } else if (month === 11 && day === 2) {
        bgImage = "url(../static/img/duckymode2.png)";
    } else if ([11, 12].includes(month)) {
        bgImage = "url(../static/img/wintermode.png)";
    } else if (isDay) {
        bgImage = "url(../static/img/lightmodeF.png)";
    }
    $("body").css("background-image", bgImage);

    try {
        const res = await fetch('/api/calendar', { method: 'GET', mode: 'cors' });
        const data = await res.json();
        $("#calendar").html(data.data);

        if (is_golden){
            setNewTheme("theme-golden")
        } else if (isDay) {
            setNewTheme("theme-light")
        } else{
            setNewTheme("theme-dark")
        }

        $("#datadog").attr('src', ddog_dashboard + Date().now());

    } catch (err) {
        console.log(err);
    }
}

async function mediumUpdate() {
    try {
        const [wikiRes, announcementRes] = await Promise.all([
            fetch('/api/wikithought', { method: 'GET', mode: 'cors' }),
            fetch('/api/announcement', { method: 'GET', mode: 'cors' })
        ]);
        const wikiData = await wikiRes.json();
        const announcementData = await announcementRes.json();
        $("#wikipageheader").text(wikiData.page + " - csh/Wikithoughts")
        $("#wikipagetext").text(wikiData.content);
        $("#announcement").text(announcementData.data.substring(0, 910));
    } catch (err) {
        console.log(err);
    }
}



mediumUpdate();
longUpdate();

setInterval(longUpdate, 60000);
setInterval(mediumUpdate, 22000);
setInterval(() => { if (globalThis.__weatherwidget_init) globalThis.__weatherwidget_init(); }, 1800000);