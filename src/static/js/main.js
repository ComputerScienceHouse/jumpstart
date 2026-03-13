async function longUpdate() {
    const date = new Date();
    const hour = date.getHours();
    const month = date.getMonth() + 1;
    const day = date.getDate();

    let bgImage = "url(../static/img/darkmodeF.png)";
    
    if (month === 2 && [12, 13, 14].includes(day)) {
        bgImage = "url(../static/img/valentinemode.png)";
    } else if (month === 3 && day === 13) {
        bgImage = "url(../static/img/jumpstartbang.png)";
    } else if (month === 10 && [29, 30, 31].includes(day)) {
        bgImage = "url(../static/img/spookymode.png)";
    } else if (month === 11 && day === 2) {
        bgImage = "url(../static/img/duckymode2.png)";
    } else if ([11, 12].includes(month)) {
        bgImage = "url(../static/img/wintermode.png)";
    } else if (hour > 9 && hour < 18) {
        bgImage = "url(../static/img/lightmodeF.png)";
    }
    $("body").css("background-image", bgImage);

    try {
        const res = await fetch('/api/calendar', { method: 'GET', mode: 'cors' });
        const data = await res.json();
        $("#calendar").html(data.data);

        const isDay = hour > 9 && hour < 18;
        const panelBody = $(".panel-body");
        const plugBody = $(".plug-body");
        const wikiPages = $(".wikithoughts-text-body");
        const announcementsBody = $(".announcements-text-body");
        const calendarFrame = $(".calendar-frame-lvl1");
        const calendarTextDate = $(".calendar-text-date");
        const calendarText = $(".calendar-text");

        if (isDay) {
            panelBody.css("background-color", "white");
            plugBody.css("background-color", "white");
            wikiPages.css({ "background-color": "white", "color": "black" });
            announcementsBody.css("color", "black");
            calendarFrame.css("background-color", "white");
            calendarTextDate.css("color", "black");
            calendarText.css("color", "black");
        } else {
            panelBody.css("background-color", "black");
            plugBody.css("background-color", "black");
            wikiPages.css({ "background-color": "black", "color": "white" });
            announcementsBody.css("color", "white");
            calendarFrame.css("background-color", "black");
            calendarTextDate.css("color", "white");
            calendarText.css("color", "white");
        }

        $("#datadog").attr('src', ddog_dashboard + new Date().now());

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

async function shortUpdate() {
    try {
        const res = await fetch('/api/harold', { method: 'GET', mode: 'cors' });
        const data = await res.json();
        $("#harold-file-name").text(data.data);
    } catch (err) {
        console.log(err);
    }
}

shortUpdate();
mediumUpdate();
longUpdate();

setInterval(longUpdate, 360000);
setInterval(mediumUpdate, 13000);
setInterval(shortUpdate, 4000);
setInterval(() => { if (window.__weatherwidget_init) window.__weatherwidget_init(); }, 1800000);