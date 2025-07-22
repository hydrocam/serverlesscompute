from datetime import datetime

def extract_datetime_from_filename(filename):
    try:
        date_str = filename.split('_')[2]
        time_str = filename.split('_')[3].split('.')[0]
        datetime_str = f"{date_str} {time_str.replace('-', ':')}"
        datetime_obj = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
        return datetime_obj.strftime('%Y-%m-%d %H:%M:%S'), datetime_obj.strftime('%Y'), datetime_obj.strftime('%B')
    except Exception as e:
        print(f'Error extracting datetime from filename: {e}')
        return None, None, None