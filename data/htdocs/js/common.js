/*
 * common.js
 */

function formatTime(time)
{
    var sec = time % 60;
    if (sec < 10)
        sec = "0" + sec;
    var min = parseInt(time/60);
    if (min > 60) {
        var hour = parseInt(min/60);
        min = min % 60;
        if (min < 10)
            min = "0" + min;
        return hour + ":" + min + ":" + sec;
        }
    else {
        if (min < 10)
            min = "0" + min;
        return min + ":" + sec;
        }
}

function urlencode(str) {
  var output = new String(encodeURIComponent(str));
  output = output.replace(/'/g,"%27");
  return output;
}

function eregReplace(search, replace, subject) {
	return subject.replace(new RegExp(search,'g'), replace);
}

