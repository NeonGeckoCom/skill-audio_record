# <img src='https://0000.us/klatchat/app/files/neon_images/icons/neon_skill.png' card_color="#FF8600" width="50" style="vertical-align:bottom">Audio Record

## Summary

Record and playback short audio clips with Neon.

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
