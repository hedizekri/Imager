// Imager B-roll to Sequence - Premiere Pro ExtendScript
// Run from VS Code ExtendScript (Run without Debugging). No ScriptUI in Premiere.

var TICKS_PER_SECOND = 254016000000;
var PRESETS = {
  vertical: { width: 1080, height: 1920, fps: 30 },
  horizontal: { width: 1920, height: 1080, fps: 30 }
};
var VIDEO_PATTERN = /^(\d{2})-(\d{2})-(\d{2})-(\d{2})/;
var AUDIO_EXT = [".mp3", ".wav", ".m4a", ".aiff"];
var VIDEO_EXT = [".mp4", ".mov", ".avi", ".mkv"];

function showDialog() {
  var f = File.openDialog("Select any file in the Imager output folder", "*", false);
  if (!f) return;
  var folderPath = f.parent.fsName;
  var useVertical = confirm("Use Vertical (TikTok 9:16)?\nOK = Vertical, Cancel = Horizontal (YouTube 16:9)");
  runMain(folderPath, useVertical ? "vertical" : "horizontal");
}

function runMain(folderPath, presetKey) {
  var folder = new Folder(folderPath);
  if (!folder.exists) {
    alert("Folder not found: " + folderPath);
    return;
  }

  var preset = PRESETS[presetKey];
  if (!preset) {
    alert("Unknown preset.");
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
    if (AUDIO_EXT.indexOf(ext) >= 0) audioFiles.push(f);
    if (VIDEO_EXT.indexOf(ext) >= 0) videoFiles.push(f);
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

  var project = app.project;
  if (!project) {
    alert("No active project. Open or create a project first.");
    return;
  }

  var sequenceName = folder.name;
  var sequenceId = "imager-" + sequenceName.replace(/\s/g, "_") + "-" + Math.floor(Math.random() * 1e9);
  var seq = project.createNewSequence(sequenceName, sequenceId);
  if (!seq) {
    alert("Could not create sequence.");
    return;
  }

  try {
    var settings = seq.getSettings();
    settings.frameSizeHorizontal = preset.width;
    settings.frameSizeVertical = preset.height;
    seq.setSettings(settings);
  } catch (e) {
    // Some versions may not allow changing size; continue
  }

  var bin = project.rootItem.createBin("Imager Import");
  var toImport = [audioFiles[0]].concat(parsed.map(function(p) { return p.file; }));
  var pathList = toImport.map(function(f) { return f.fsName; });
  project.importFiles(pathList, 1, bin, false);

  var audioFileName = audioFiles[0].name;
  var n = bin.children.numItems;
  var audioItem = null;
  var videoItemsByName = {};
  for (var j = 0; j < n; j++) {
    var item = bin.children[j];
    if (item.type !== 1 && item.name) {
      if (item.name === audioFileName)
        audioItem = item;
      else
        videoItemsByName[item.name] = item;
    }
  }
  if (!audioItem) {
    alert("Could not find imported audio in project.");
    return;
  }

  app.project.activeSequence = seq;
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

  alert("Sequence \"" + sequenceName + "\" created with " + parsed.length + " video clip(s) and audio.");
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
