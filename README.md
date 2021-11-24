# <img src='https://0000.us/klatchat/app/files/neon_images/icons/neon_skill.png' card_color="#FF8600" width="50" style="vertical-align:bottom">Audio Record

## Summary

Record and playback short audio clips with Neon.

## Requirements

    psutil==5.2.1


Which should be automatically installed with Neon. However, you can also manually install the package by running:

    source ${core}/.venv/bin/activate  
    pip --no-cache-dir install psutil

Alternatively:

    source ${core}/.venv/bin/activate
    cd ${skills}/audio-record.neon/  
    pip --no-cache-dir install requirements.txt


## Description

This Skill records audio from the microphone and allows you to play back that recording.

Note that this Skill is particularly useful when trying to diagnose microphone issues because it allows you to "hear" 
what Neon is hearing - For example, if you have multiple audio inputs or are working on the new skill that requires pure microphone feed.

## Examples

Say `“Hey Neon”` if you are in the wake words mode, otherwise include `"Neon"` at the beginning of your request.
You can request a recording with a particular name and/or duration, but neither are required. For example:
- "record audio"
- "record audio for 30 seconds"
- "record my daily prescriptions"
- "record my daily prescriptions for 1 minute"
You can have as many recordings [as your memory allows.](https://www.linux.com/blog/linux-101-check-disk-space-command)

## Location

    ${skills}/audio-record.neon

## Files
<details>
<summary>Click to expand.</summary>
<br>

    ./requirements.txt  
    ./__init__.py  
    ./test  
    ./test/intent  
    ./test/intent/001.stop.json  
    ./test/intent/000.record.for.1.second.json  
    ./test/intent/002.start.recording.for.1.second.json  
    ./test/intent/003.stop.json  
    ./test/intent/sample1.intent.json  
    ./test/intent/004.play.recording.json  
    ./test/intent/sample4.intent.json  
    ./test/intent/sample8.intent.json  
    ./test/intent/sample7.intent.json  
    ./test/intent/sample2.intent.json  
    ./test/intent/sample6.intent.json  
    ./test/intent/005.stop.json  
    ./test/intent/sample5.intent.json  
    ./test/intent/006.erase.recording.json  
    ./test/intent/sample3.intent.json  
    ./.gitignore  
    ./settings.json  
    ./locale  
    ./locale/en-us  
    ./locale/en-us/StartRecording.intent  
    ./locale/en-us/PlayRecording.intent  
    ./locale/en-us/Recording.voc  
    ./locale/en-us/Delete.voc  
    ./locale/en-us/Play.voc  
    ./locale/en-us/audio.record.start.duration.dialog  
    ./locale/en-us/audio.record.disk.full.dialog  
    ./locale/en-us/audio.record.no.recording.dialog  
    ./locale/en-us/audio.record.removed.dialog  
    ./locale/de-de  
    ./locale/de-de/Recording.voc  
    ./locale/de-de/Delete.voc  
    ./locale/de-de/Play.voc  
    ./locale/de-de/audio.record.start.duration.dialog  
    ./locale/de-de/audio.record.disk.full.dialog  
    ./locale/de-de/audio.record.no.recording.dialog  
    ./locale/de-de/audio.record.removed.dialog  
    ./locale/it-it  
    ./locale/it-it/Recording.voc  
    ./locale/it-it/Delete.voc  
    ./locale/it-it/Play.voc  
    ./locale/it-it/audio.record.start.duration.dialog  
    ./locale/it-it/audio.record.disk.full.dialog  
    ./locale/it-it/audio.record.no.recording.dialog  
    ./locale/it-it/audio.record.removed.dialog  
    ./dialog  
    ./dialog/en-us  
    ./dialog/en-us/audio.record.stop.play.dialog  
    ./dialog/en-us/audio.record.stop.dialog  
    ./dialog/en-us/audio.record.start.dialog  
    ./dialog/en-us/audio.record.start.duration.dialog  
    ./dialog/en-us/audio.record.disk.full.dialog  
    ./dialog/en-us/audio.record.no.recording.dialog  
    ./dialog/en-us/audio.record.removed.dialog  
    ./dialog/it-it  
    ./dialog/it-it/audio.record.stop.play.dialog  
    ./dialog/it-it/audio.record.stop.dialog  
    ./dialog/it-it/audio.record.start.dialog  
    ./dialog/it-it/audio.record.start.duration.dialog  
    ./dialog/it-it/audio.record.disk.full.dialog  
    ./dialog/it-it/audio.record.no.recording.dialog  
    ./dialog/it-it/audio.record.removed.dialog  
    ./vocab  
    ./vocab/en-us  
    ./vocab/en-us/AudioRecordSkillDeleteVerb.voc  
    ./vocab/en-us/Neon.voc  
    ./vocab/en-us/AudioRecordSkillPlayVerb.voc  
    ./vocab/en-us/AudioRecordSkillKeyword.voc  
    ./vocab/en-us/AudioRecordSkillStopVerb.voc  
    ./vocab/it-it  
    ./vocab/it-it/AudioRecordSkillDeleteVerb.voc  
    ./vocab/it-it/AudioRecordSkillPlayVerb.voc  
    ./vocab/it-it/AudioRecordSkillKeyword.voc  
    ./vocab/it-it/AudioRecordSkillStopVerb.voc  
    ./LICENSE  
    ./README.md
</details>

## Class Diagram

[Click Here](https://0000.us/klatchat/app/files/neon_images/class_diagrams/audio-record.png)

## Available Intents
<details>
<summary>Click to expand.</summary>
<br>

### AudioRecordSkillDeleteVerb.voc

    delete  
    erase  
    remove

  

### Neon.voc

    neon  
    leon  
    nyan

### AudioRecordSkillPlayVerb.voc

    run  
    replay  
    playback  
    reproduce  
    running  
    playing  
    replaying  
    reproducing

### AudioRecordSkillKeyword.voc

    record  
    recording

### AudioRecordSkillStopVerb.voc

    end  
    stop  
    cancel

  

### AudioRecordSkillDeleteVerb.voc

    cancella  
    elimina  
    rimuovi

  

### AudioRecordSkillPlayVerb.voc

    suona  
    suonare  
    riproduci  
    riprodurre

  

### AudioRecordSkillKeyword.voc

    registra  
    registrazione

  

### AudioRecordSkillStopVerb.voc

    fine  
    stop  
    ferma

</details>

## Details

### Text

        Neon start recording
        >> Starting audio recording for thirty seconds
        
        Neon record 30 minutes of audio
        >> Recording audio for thirty minutes
        
        Neon stop recording
        >> Audio recording stopped.

        Neon playback recording
        >> *audio playback*
        
        Neon erase audio recording
        >> Deleting


### Picture

### Video

## Troubleshooting

This skill is designed to help troubleshoot microphone issues. If you have any problems with skill’s execution, try executing the subprocess command, which is called from the skill, after filling in the placeholders -

    subprocess.Popen(["arecord", "-r", str(rate), "-c", str(channels), "-d", str(duration), file_path])

Manually and see if you have similar results. You microphone issue may be system-wide or limited to Neon and this will help determine that.

  

## Contact Support

Use the [link](https://neongecko.com/ContactUs) or [submit an issue on GitHub](https://help.github.com/en/articles/creating-an-issue)

## Credits
[Mycroft AI](https://github.com/MycroftAI)
[NeonDaniel](https://github.com/NeonDaniel)
[reginaneon](https://github.com/reginaneon)

## Category
**Configuration**

## Tags
#audio
#record
#record-audio
#microphone
#configuration
