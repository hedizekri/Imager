// Imager B-roll to Sequence - Premiere Pro ExtendScript
// Run from VS Code ExtendScript (Run without Debugging). No ScriptUI in Premiere.

var TICKS_PER_SECOND = 254016000000;
var VIDEO_PATTERN = /^(\d{2})-(\d{2})-(\d{2})-(\d{2})/;
var AUDIO_EXT = [".mp3", ".wav", ".m4a", ".aiff"];
var VIDEO_EXT = [".mp4", ".mov", ".avi", ".mkv"];

function inArray(arr, val) {
  for (var i = 0; i < arr.length; i++) if (arr[i] === val) return true;
  return false;
}

function showDialog() {
  var f = File.openDialog("Select any file in the Imager output folder", "*", false);
  if (!f) return;
  runMain(f.parent.fsName);
}

function runMain(folderPath) {
  var folder = new Folder(folderPath);
  if (!folder.exists) {
    alert("Folder not found: " + folderPath);
    return;
  }

  var project = app.project;
  if (!project) {
    alert("No active project. Open or create a project first.");
    return;
  }
  var seq = project.activeSequence;
  if (!seq) {
    alert("Create a sequence and set its format (vertical/horizontal) in Premiere, then select it and run the script again.");
    return;
  }

  var files = folder.getFiles();
  var audioFiles = [];
  var videoFiles = [];
  for (var i = 0; i < files.length; i++) {
    var f = files[i];
    if (f.constructor.name !== "File") continue;
    var name = f.name.toLowerCase();
    var ext = "";
    var idx = name.lastIndexOf(".");
    if (idx >= 0) ext = name.substring(idx);
    if (inArray(AUDIO_EXT, ext)) audioFiles.push(f);
    if (inArray(VIDEO_EXT, ext)) videoFiles.push(f);
  }

  if (audioFiles.length !== 1) {
    alert("Folder must contain exactly one audio file. Found: " + audioFiles.length);
    return;
  }
  if (videoFiles.length < 1) {
    alert("Folder must contain at least one video file.");
    return;
  }

  var parsed = parseVideoFilenames(videoFiles);
  if (parsed.length === 0) {
    alert("No video files match the timestamp format MM-SS-MM-SS (e.g. 00-00-00-06-name.mp4).");
    return;
  }
  if (parsed.length < videoFiles.length) {
    alert("Skipped " + (videoFiles.length - parsed.length) + " video(s) without timestamp in filename.");
  }

  var bin = project.rootItem.createBin("Imager Import");
  var toImport = [audioFiles[0]];
  for (var t = 0; t < parsed.length; t++) toImport.push(parsed[t].file);
  var pathList = [];
  for (var u = 0; u < toImport.length; u++) pathList.push(toImport[u].fsName);
  project.importFiles(pathList, 1, bin, false);

  var audioFileName = audioFiles[0].name;
  var audioFileNameLower = audioFileName.toLowerCase();
  var n = bin.children.numItems;
  var audioItem = null;
  var videoItemsByName = {};
  for (var j = 0; j < n; j++) {
    var item = bin.children[j];
    if (!item.name) continue;
    var nameLower = item.name.toLowerCase();
    var ext = nameLower.indexOf(".") >= 0 ? nameLower.substring(nameLower.lastIndexOf(".")) : "";
    if (nameLower === audioFileNameLower || (!audioItem && inArray(AUDIO_EXT, ext)))
      audioItem = item;
    else
      videoItemsByName[item.name] = item;
  }
  if (!audioItem) {
    alert("Could not find imported audio in project.");
    return;
  }

  var ticksZero = "0";
  seq.audioTracks[0].overwriteClip(audioItem, ticksZero);

  var timebase = parseFloat(seq.timebase) || TICKS_PER_SECOND / 30;
  for (var p = 0; p < parsed.length; p++) {
    var entry = parsed[p];
    var item = videoItemsByName[entry.file.name];
    if (!item) continue;
    var startTicks = Math.round(entry.startSec * TICKS_PER_SECOND).toString();
    var intervalLen = entry.endSec - entry.startSec;
    var durationSec = getItemDurationSeconds(item);
    if (durationSec === null) durationSec = intervalLen;
    if (durationSec >= intervalLen) {
      try {
        item.setInPoint(0);
        item.setOutPoint(intervalLen);
      } catch (err) {}
    }
    seq.videoTracks[0].overwriteClip(item, startTicks);
  }

  alert("Done. Placed " + parsed.length + " video clip(s) and audio into \"" + seq.name + "\".");
}

function parseVideoFilenames(videoFiles) {
  var result = [];
  for (var i = 0; i < videoFiles.length; i++) {
    var f = videoFiles[i];
    var match = f.name.match(VIDEO_PATTERN);
    if (!match) continue;
    var startSec = parseInt(match[1], 10) * 60 + parseInt(match[2], 10);
    var endSec = parseInt(match[3], 10) * 60 + parseInt(match[4], 10);
    if (endSec <= startSec) endSec = startSec + 1;
    result.push({ file: f, startSec: startSec, endSec: endSec });
  }
  result.sort(function(a, b) { return a.startSec - b.startSec; });
  return result;
}

function getItemDurationSeconds(item) {
  try {
    if (item.getMediaDuration) return item.getMediaDuration();
    if (item.outPoint !== undefined && item.inPoint !== undefined) {
      var outTicks = parseFloat(String(item.outPoint));
      var inTicks = parseFloat(String(item.inPoint));
      if (!isNaN(outTicks) && !isNaN(inTicks)) return (outTicks - inTicks) / TICKS_PER_SECOND;
    }
  } catch (e) {}
  return null;
}

showDialog();
