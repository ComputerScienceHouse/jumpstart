let currentPageTheme = "";
let currentDatadogTheme = "";
let currentWeatherTheme = "";

/* 
    The struct of all the different themes. 
    - Page: The .css page theme to be loaded (make sure they start with theme-)!
    - Datadog: The datadog theme to be loaded, can either be light or dark
    - Weather: The theme of the weather widget, all the styles can be found here: https://weatherwidget.io/
*/
const allThemes = {
    golden: {
        page: "theme-golden",
        datadog: "dark",
        weather: "dark"
    },
    dark: {
        page: "theme-dark",
        datadog: "dark",
        weather: "kitty"
    },
    light: {
        page: "theme-light",
        datadog: "light",
        weather: "kitty"
    }
};


function setDatadogTheme(newTheme) {
    if (newTheme === currentDatadogTheme) {
        return;
    }
    currentDatadogTheme = newTheme;

    const iframe = document.getElementById("datadog");
    const url = new URL(iframe.src);
    url.searchParams.set("theme", newTheme);
    iframe.src = url.toString();
}

function setWeatherTheme(newTheme) {
    if (newTheme === currentWeatherTheme) {
        return;
    }
    currentWeatherTheme = newTheme;
    const widget = document.getElementById("weather-image");
    widget.setAttribute("data-theme", newTheme);
    
    if (globalThis.weatherWidget) {
        widget.innerHTML = widget.innerHTML;
        weatherWidget.init();
    }
}

function setNewPageTheme(newTheme) {
    if (newTheme === currentPageTheme) {
        return;
    }
    currentPageTheme = newTheme;

    document.body.classList.forEach(cls => {
    if (cls.startsWith('theme-')) {
        document.body.classList.remove(cls);
    }});

    document.body.classList.toggle(newTheme); 
}

async function longUpdate() {
    const date = new Date();
    const hour = date.getHours();
    const month = date.getMonth() + 1;
    const day = date.getDate();
    const isDay = (hour > 9 && hour < 18);

    let is_golden = (month === 4 && [9, 10, 11, 12].includes(day));
    let bgImage = "url(../static/img/darkmodeF.png)";
    
    if (month === 2 && [12, 13, 14].includes(day)) {
        bgImage = "url(../static/img/valentinemode.png)";
    } else if (month === 3 && day === 13) {
        bgImage = "url(../static/img/jumpstartbang.png)";
    } else if (is_golden) {
        bgImage = "url(../static/img/goldenmode.png)";
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

        let themeToLoad = "dark";
        if (is_golden){
            themeToLoad = "golden";
        } else if (isDay) {
            themeToLoad = "light";
        }

        setNewPageTheme(allThemes[themeToLoad].page);
        setDatadogTheme(allThemes[themeToLoad].datadog);
        setWeatherTheme(allThemes[themeToLoad].weather);


        const res = await fetch('/api/calendar', { method: 'GET', mode: 'cors' });
        const data = await res.json();
        $("#calendar").html(data.data);
        
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
setInterval(() => { 
    if (globalThis.__weatherwidget_init) 
        globalThis.__weatherwidget_init(); 
}, 1800000);