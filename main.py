#!/usr/bin/env python
# author: Iraj Jelodari

import datetime
import codecs
import re
import os

RED = '#FF003B'
BLUE = '#00ADFF'
GREEN = '#B4FF00'
WHITE = '#FFFFFF'
YELLOW = '#FFEB00'

TIME_PATTERN = r'\d{1,2}:\d{1,2}:\d{1,2},\d{1,5} --> \d{1,2}:\d{1,2}:\d{1,2},\d{1,5}\r\n'


class Merger():
    """
    SRT Merger allows you to merge subtitle files, no matter what language
    are the subtitles encoded in. The result of this merge will be a new subtitle
    file which will display subtitles from each merged file.
    """

    def __init__(self, output_path=".", output_name='subtitle_name.srt', output_encoding='utf-8'):
        self.timestamps = []
        self.subtitles = []
        self.lines = []
        self.output_path = output_path
        self.output_name = output_name
        self.output_encoding = output_encoding

    def _insert_bom(self, content, encoding):
        encoding = encoding.replace('-', '')\
            .replace('_', '')\
            .replace(' ', '')\
            .upper()
        if encoding in ['UTF64LE', 'UTF16', 'UTF16LE']:
            return codecs.BOM + content
        if encoding in ['UTF8']:
            return codecs.BOM_UTF8 + content
        if encoding in ['UTF32LE']:
            return codecs.BOM_UTF32_LE + content
        if encoding in ['UTF64BE']:
            return codecs.BOM_UTF64_BE + content
        if encoding in ['UTF16BE']:
            return codecs.BOM_UTF32_BE + content
        if encoding in ['UTF32BE']:
            return codecs.BOM_UTF32_BE + content
        if encoding in ['UTF32']:
            return codecs.BOM_UTF32 + content
        return content

    def _set_subtitle_color(self, subtitle, color):
        """
        Set a color for subtitle
        """
        return '<font color="{!s}">{!s}</font>'.format(
            color, subtitle) if color else subtitle

    def _put_subtitle_top(self, subtitle):
        """
        Put the subtitle at the top of the screen
        """
        return '{\\an8}' + subtitle

    def _split_dialogs(self, dialogs, subtitle, color=None, top=False):
        for dialog in dialogs:
            if dialog.startswith('\r\n'):
                dialog = dialog.replace('\r\n', '', 1)
            if dialog.startswith('\n'):
                dialog = dialog[1:]
            if dialog == '' or dialog == '\n' or dialog.rstrip().lstrip() == '':
                continue
            try:
                if dialog.startswith('\r\n'):
                    dialog = dialog[2:]
                time = dialog.split('\n', 2)[1].split('-->')[0].split(',')[0]
            except Exception as e:
                continue
            timestamp = datetime.datetime.strptime(
                time, '%H:%M:%S').timestamp()
            text_and_time = dialog.split('\n', 1)[1]
            texts = text_and_time.split('\n')[1:]
            time = text_and_time.split('\n')[0]
            text = ""
            for t in texts:
                text += t + '\n'
            if text == '' or text == '\n':
                continue
            text = self._set_subtitle_color(text, color)
            if top is True:
                text = self._put_subtitle_top(text)
            text_and_time = '%s\n%s\n' % (time, text)
            # Previuos dialog for same timestamp
            prev_dialog_for_same_timestamp = subtitle['dialogs'][timestamp] = subtitle['dialogs'].get(
                timestamp, '')
            prev_dialog_without_timestamp = re.sub(
                TIME_PATTERN, '', prev_dialog_for_same_timestamp)
            if re.findall(TIME_PATTERN, text_and_time):
                time = re.findall(TIME_PATTERN, text_and_time)[0]
            subtitle['dialogs'][timestamp] = text_and_time + \
                prev_dialog_without_timestamp
            self.timestamps.append(timestamp)

    def _encode(self, text):
        codec = self.output_encoding
        try:
            return bytes(text, encoding=codec)
        except Exception as e:
            print('Problem in "%s" to encoing by %s. \nError: %s' %
                  (repr(text), codec, e))
            return b'An error has been occured in encoing by specifed `output_encoding`'

    def add(self, subtitle_address, codec="utf-8", color=WHITE, top=False):
        subtitle = {
            'address': subtitle_address,
            'codec': codec,
            'color': color,
            'dialogs': {}
        }
        with open(subtitle_address, 'r') as file:
            data = file.buffer.read().decode(codec)
            dialogs = re.split('\r\n\r|\n\n', data)
            subtitle['data'] = data
            subtitle['raw_dialogs'] = dialogs
            self._split_dialogs(dialogs, subtitle, color, top)
            self.subtitles.append(subtitle)

    def get_output_path(self):
        if self.output_path.endswith('/'):
            return self.output_path + self.output_name
        return self.output_path + '/' + self.output_name

    def merge(self):
        self.lines = []
        self.timestamps = list(set(self.timestamps))
        self.timestamps.sort()
        count = 1
        for t in self.timestamps:
            for sub in self.subtitles:
                if t in sub['dialogs'].keys():
                    line = self._encode(sub['dialogs'][t].replace('\n\n', ''))
                    if count == 1:
                        byteOfCount = self._insert_bom(
                            bytes(str(count), encoding=self.output_encoding),
                            self.output_encoding
                        )
                    else:
                        byteOfCount = '\n'.encode(
                            self.output_encoding) + bytes(str(count), encoding=self.output_encoding)
                    if sub['dialogs'][t].endswith('\n') != True:
                        sub['dialogs'][t] = sub['dialogs'][t] + '\n'
                    dialog = byteOfCount + \
                        '\n'.encode(self.output_encoding) + line
                    self.lines.append(dialog)
                    count += 1
        if self.lines[-1].endswith(b'\x00\n\x00'):
            self.lines[-1] = self.lines[-1][:-3] + b'\x00'
        if self.lines[-1].endswith(b'\n'):
            self.lines[-1] = self.lines[-1][:-1] + b''
        with open(self.get_output_path(), 'w', encoding=self.output_encoding) as output:
            output.buffer.writelines(self.lines)
            print("'%s'" % (output.name), 'created successfully.')

def find_file(directory , extension):
    files = [file for file in os.listdir(directory) if file.endswith(extension)]
    if len(files) == 1:
        return files[0]
    elif len(files) == 0:
        print(f"Error: No {extension} file found in {directory}.")
    else:
        print(f"Error: Multiple {extension} files found. Please make sure only one exists.")

def find_and_merge(directory, extensions=["ar.srt", "zh.srt"]):
    first_srt_file = find_file(directory, extensions[0])
    second_srt_file = find_file(directory, extensions[1])
    if first_srt_file and second_srt_file:
        output_name = os.path.splitext(first_srt_file)[0] + "_zh.srt"
        m = Merger(output_name=output_name)
        os.chdir(directory)
        m.add(second_srt_file, top=True)
        m.add(first_srt_file, color='#FF9300')
        m.merge()
        processed = os.path.join(directory, 'bilingual.txt')
        with open(processed, 'w') as file:
            # You can add content to the file if needed
            file.write("bilingual")
        print(f"Merged {first_srt_file} and {second_srt_file} into {output_name}.")

def bilingual(directory):
    file_path = os.path.join(directory, 'bilingual.txt')
    if os.path.exists(file_path):
        print(f"'bilingual.txt' found in directory: {directory}")
    else:
        find_and_merge(directory)

def process_subdirectories(root_path):
    if not os.path.isdir(root_path):
        print(f"{root_path} is not a valid directory.")
        return
    items = os.listdir(root_path)
    for item in items:
        item_path = os.path.join(root_path, item)
        if os.path.isdir(item_path):
            bilingual(item_path)


if __name__ == "__main__":
    process_subdirectories('<PATH>')