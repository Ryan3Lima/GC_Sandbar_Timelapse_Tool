# GCSandbarTimelapse.py

##------------------------- load libraries--------------------#
import re
import os
import cv2
import glob
from datetime import datetime, time, timedelta
import matplotlib.pyplot as plt
from pathlib import Path
import numpy as np
from pprint import pprint

'''
This Python script is designed to facilitate the creation of timelapse videos from the Grand Canyon Sandbar Imagery
making it suitable for applications such as monitoring sandbar changes over time.

# last update 7/24/24, based on workflow in GC_SandbarTimelapseCreator.ipynb



Environment Setup: Ensure that all dependencies (e.g., cv2, matplotlib) are installed in your Jupyter environment.
Path Adjustments: Paths (like parent_dir and output_dir) may need to be adjusted depending on the environment in which your notebook is running.
'''



#--------------Set Variables----------------------------------------------------#
#parent_dir = os.path.abspath('M:\\Remote Cameras\\full_res')




## ----------------------Functions------------------------------------------##

def find_sandbar_dirs(parent_dir):
    """
    Traverse the given parent directory, find subdirectories and files matching specific patterns,
    and return information about the directories.

    Parameters:
    - parent_dir: The directory to traverse.

    Returns:
    - results: A dictionary containing:
        - 'site_names': List of site names (keys for 'sandbar_info').
        - 'sandbar_dirs': List of directories that match the specified patterns.
        - 'sandbar_info': Dictionary with detailed info for each directory.
    """
    sandbar_dirs = []
    sandbar_info = {}
    site_names = []
    dir_pattern = re.compile(r'RC\d{4}[RL][a-z]?')
    file_pattern = re.compile(r'RC\d{4}[RL][a-z]?_(\d{8})_(\d{4})(_web)?\.(jpg|jpeg|JPG|JPEG)$')

    for root, dirs, files in os.walk(parent_dir):
        for dir in dirs:
            if dir_pattern.match(dir):
                dir_path = os.path.join(root, dir)
                matching_files = [f for f in os.listdir(dir_path) if file_pattern.match(f)]
                if matching_files:
                    sandbar_dirs.append(dir_path)
                    site_name = os.path.basename(dir_path)
                    site_names.append(site_name)
                    matching_files.sort()

                    # Extract dates and times from filenames
                    start_file = matching_files[0]
                    end_file = matching_files[-1]

                    start_match = file_pattern.match(start_file)
                    end_match = file_pattern.match(end_file)

                    if start_match and end_match:
                        start_date_time = datetime.strptime(start_match.group(1) + start_match.group(2), '%Y%m%d%H%M')
                        end_date_time = datetime.strptime(end_match.group(1) + end_match.group(2), '%Y%m%d%H%M')

                        sandbar_info[site_name] = {
                            'number_of_files': len(matching_files),
                            'start_date_time': start_date_time,
                            'end_date_time': end_date_time
                        }

                        # Print the information
                        print(f"Directory: {dir_path} ({site_name}) contains {len(matching_files)} matching files.")
                        print(f"  Start date-time: {start_date_time}")
                        print(f"  End date-time: {end_date_time}")

    return {'site_names': site_names, 'sandbar_dirs': sandbar_dirs, 'sandbar_info': sandbar_info}
    pass


def get_image_files(directory):
    """
    Get a list of image file paths from the given directory.
    Supports .jpg, .JPG, .jpeg, .JPEG file extensions.
    """
    extensions = ['jpg', 'JPG', 'jpeg', 'JPEG']
    files = []
    for ext in extensions:
        files.extend(glob.glob(os.path.join(directory, f'*.{ext}')))
    return files
    pass


## 2.
'''
def parse_filename(filename):
    """
    Parse the date and time from the filename.
    """
    file_pattern = re.compile(r'RC\d{4}[RL][a-z]?_(\d{8})_(\d{4})(_web)?\.(jpg|jpeg|JPG|JPEG)$')
    match = file_pattern.match(filename)
    if match:
        return datetime.strptime(match.group(1) + match.group(2), '%Y%m%d%H%M')
    return None
'''
def parse_filename(filepath):
    """
    Parse the date and time from the filename.
    """
    filename = os.path.basename(filepath)  # Extract just the filename
    file_pattern = re.compile(r'RC\d{4}[RL][a-z]?_(\d{8})_(\d{4})(_web)?\.(jpg|jpeg|JPG|JPEG)$')
    match = file_pattern.match(filename)
    if match:
        return datetime.strptime(match.group(1) + match.group(2), '%Y%m%d%H%M')
    return None
    pass
## 3.
def get_file_size(file_path):
    """
    Get and print the file size of the given image file.
    """
    size_bytes = os.path.getsize(file_path)
    size_kb = size_bytes / 1024
    print(f"File: {file_path}, Size: {size_kb:.2f} KB")
    return size_kb
    pass

## 4.
def resize_image(image, scale_percent):
    """
    Resize the given image by the specified scale percentage.
    """
    width = int(image.shape[1] * scale_percent / 100)
    height = int(image.shape[0] * scale_percent / 100)
    dim = (width, height)
    return cv2.resize(image, dim, interpolation=cv2.INTER_AREA)
    pass

## 5
def filter_images(folder_path, start_time_str, end_time_str, start_year=None, end_year=None):
    """
    Filter images in the folder based on the specified time range and optionally by year.

    Parameters:
    - folder_path (str): Path to the directory containing images.
    - start_time_str (str): Start time to filter images, in 24-hour 4-digit format (e.g., '0930').
    - end_time_str (str): End time to filter images, in 24-hour 4-digit format (e.g., '1123').
    - start_year (int, optional): Start year to include images from. None means no lower year limit.
    - end_year (int, optional): End year to include images until. None means no upper year limit.

    Returns:
    - Dictionary with details:
      {
          "total_photos": int,
          "start_date": str,
          "end_date": str,
          "retained_files": list,
          "missing_dates": list
      }
    """
    # Convert start_time_str and end_time_str to datetime.time objects
    start_time = time(int(start_time_str[:2]), int(start_time_str[2:]))
    end_time = time(int(end_time_str[:2]), int(end_time_str[2:]))

    filtered_files = []
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        file_datetime = parse_filename(filename)
        if file_datetime:
            # Check if the file's datetime falls within the specified year and time range
            if ((start_year is None or file_datetime.year >= start_year) and
                (end_year is None or file_datetime.year <= end_year) and
                start_time <= file_datetime.time() <= end_time):
                filtered_files.append((file_datetime, file_path))

    # Sort the list by datetime
    filtered_files.sort(key=lambda x: x[0])

    # Retain only the first photo of each day
    files_by_date = {}
    for file_datetime, file_path in filtered_files:
        date_str = file_datetime.strftime('%Y-%m-%d')
        if date_str not in files_by_date:
            files_by_date[date_str] = (file_datetime, file_path)

    retained_files = [file[1] for file in files_by_date.values()]

    if not retained_files:
        return {
            "total_photos": 0,
            "start_date": None,
            "end_date": None,
            "retained_files": [],
            "missing_dates": []
        }

    # Determine the start and end dates
    first_date = filtered_files[0][0].date()
    last_date = filtered_files[-1][0].date()

    # Check for days with no photos
    current_date = first_date
    missing_dates = []

    while current_date <= last_date:
        if current_date.strftime('%Y-%m-%d') not in files_by_date:
            missing_dates.append(current_date)
        current_date += timedelta(days=1)

    return {
        "total_photos": len(filtered_files),
        "start_date": first_date.strftime('%Y-%m-%d'),
        "end_date": last_date.strftime('%Y-%m-%d'),
        "retained_files": retained_files,
        "missing_dates": [date.strftime('%Y-%m-%d') for date in missing_dates]
    }
    pass


## 6.
def put_date_on_image(img, date_str, font_scale=1, line_type=2, position="BL"):
    """
    Put the date string on the image at the specified position.

    Parameters:
    - img: The image on which to put the date string.
    - date_str: The date string to put on the image.
    - font_scale: Scale of the font. Increasing this value will make the text larger.
    - line_type: Thickness of the text. Increasing this value will make the text bolder.
    - position: Position where to put the text. Options are "BL" (Bottom Left), "BR" (Bottom Right),
                "TL" (Top Left), "TR" (Top Right).
    """
    # Choose the font
    font = cv2.FONT_HERSHEY_SIMPLEX

    # Determine the text size
    text_size = cv2.getTextSize(date_str, font, font_scale, line_type)[0]

    # Calculate the bottom left corner of the text based on the position
    if position == "BL":
        bottomLeftCornerOfText = (10, img.shape[0] - 10)
    elif position == "BR":
        bottomLeftCornerOfText = (img.shape[1] - text_size[0] - 10, img.shape[0] - 10)
    elif position == "TL":
        bottomLeftCornerOfText = (10, text_size[1] + 10)
    elif position == "TR":
        bottomLeftCornerOfText = (img.shape[1] - text_size[0] - 10, text_size[1] + 10)
    else:
        raise ValueError("Invalid position code. Use 'BL', 'BR', 'TL', or 'TR'.")

    # Color of the font in BGR (Blue, Green, Red)
    fontColor = (255, 255, 255)  # White color

    # Put the text on the image
    cv2.putText(img, date_str, bottomLeftCornerOfText, font, font_scale, fontColor, line_type)
    pass

def create_black_image_with_text(text, width, height):
    """
    Create a black image with the specified text.

    Parameters:
    - text: The text to put on the image.
    - width: The width of the image.
    - height: The height of the image.

    Returns:
    - img: The created image with text.
    """
    img = np.zeros((height, width, 3), np.uint8)
    font = cv2.FONT_HERSHEY_SIMPLEX
    text_size = cv2.getTextSize(text, font, 1, 2)[0]
    text_x = (img.shape[1] - text_size[0]) // 2
    text_y = (img.shape[0] + text_size[1]) // 2
    cv2.putText(img, text, (text_x, text_y), font, 1, (255, 255, 255), 2)
    return img
    pass

## 7.
def create_timelapse(site_name, filter_result, out_dir=os.getcwd(), frame_rate=7, resize_percent=25, font_scale=1, line_type=2, position="BL"):
    """
    Create a timelapse video, with options to specify an out_dir, select frame rate, and resize images by percent.
    Default framerate = 7 frames per second or 1 week per second if images are sorted by time of day to utilize a single image
    per day, which is recommended to reduce changes in water elevation and flickering from variable lighting at different times of day.

    Parameters:
    - site_name: Name of the site (used in the output file name).
    - filter_result: Dictionary containing the filter result from filter_images function.
    - out_dir: Output directory for the timelapse video.
    - frame_rate: Frame rate for the timelapse video.
    - resize_percent: Percentage to resize images.
    - font_scale: Scale of the font for the date string.
    - line_type: Thickness of the font for the date string.
    - position: Position where to put the date string ("BL", "BR", "TL", "TR").
    """
    image_files = filter_result.get("retained_files", [])
    missing_dates = filter_result.get("missing_dates", [])

    if len(image_files) == 0:
        print("No images to process.")
        return None

    # Extract start and end date-times from the filenames
    start_datetime = parse_filename(image_files[0])
    end_datetime = parse_filename(image_files[-1])

    if not start_datetime or not end_datetime:
        print("Error: Unable to parse date-time from filenames.")
        return None

    start_date_str = start_datetime.strftime('%Y%m%d%H%M')
    end_date_str = end_datetime.strftime('%Y%m%d%H%M')

    output_file = f'{site_name}_timelapse_{start_date_str}_to_{end_date_str}.mp4'
    output_file = os.path.join(out_dir, output_file)
    # Check if the output file already exists
    if os.path.exists(output_file):
        while True:
            user_input = input(f"Output file {output_file} already exists. Do you want to overwrite it? (y/n): ").strip().lower()
            if user_input == 'y':
                break
            elif user_input == 'n':
                print("Skipping timelapse creation.")
                return None
            else:
                print("Invalid input. Please enter 'y' for yes or 'n' for no.")

    # Initialize VideoWriter with the first frame's dimensions after resizing
    first_frame = cv2.imread(image_files[0])
    if resize_percent != 100:
        first_frame = resize_image(first_frame, resize_percent)
    height, width, layers = first_frame.shape
    size = (width, height)
    out = cv2.VideoWriter(output_file, cv2.VideoWriter_fourcc(*'mp4v'), frame_rate, size)

        # Process and write each image to the video
    current_date = start_datetime.date()
    end_date = end_datetime.date()
    image_index = 0

    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        if image_index < len(image_files) and parse_filename(image_files[image_index]).date() == current_date:
            filename = image_files[image_index]
            print(f'Processing image {filename} - {image_index + 1} out of {len(image_files)}')
            img = cv2.imread(filename)
            if resize_percent != 100:
                img = resize_image(img, resize_percent)
            date_time = parse_filename(filename)
            date_str_full = date_time.strftime('%Y-%m-%d %H:%M')
            put_date_on_image(img, date_str_full, font_scale=font_scale, line_type=line_type, position=position)
            image_index += 1
        else:
            print(f'No imagery available for {date_str}')
            img = create_black_image_with_text("No imagery available", width, height)
            put_date_on_image(img, date_str, font_scale=font_scale, line_type=line_type, position=position)
        out.write(img)
        current_date += timedelta(days=1)

    out.release()
    vid_size = get_file_size(output_file)

    return output_file
    pass

# Other function definitions...

if __name__ == "__main__":
    # Example usage code
    parent_dir = os.path.abspath('M:\\Remote Cameras\\full_res')
    results = find_sandbar_dirs(parent_dir)

    valid_site_names = []
    for site in results['site_names']:
        num_files = results['sandbar_info'][site]['number_of_files']
        end_time = results['sandbar_info'][site]['end_date_time']
        if num_files >= 1000 and end_time > datetime(2023, 1, 1, 12, 30):
            valid_site_names.append(site)
        else:
            print(f'Site: {site} skipped because it contains just {num_files} image files or end date-time is {end_time}')

    # Subset the 'sandbar_info' to include only valid site names
    subset_sandbar_info = {site: results['sandbar_info'][site] for site in valid_site_names}

    # Create a new 'results' dictionary including only valid site names and their corresponding directories
    subset_results = {
        'site_names': valid_site_names,
        'sandbar_dirs': [dir for dir in results['sandbar_dirs'] if os.path.basename(dir) in valid_site_names],
        'sandbar_info': subset_sandbar_info
    }

    print("Site Names:", subset_results['site_names'])
    print("Sandbar Directories:")
    pprint(subset_results['sandbar_dirs'])
    print("\nSandbar Information:")
    pprint(subset_results['sandbar_info'])
    
    start_time_str = '1100'
    end_time_str = '1300'
    start_year = 2014
    end_year = 2024

    # for site_dir in subset_results['sandbar_dirs']:
    #     site_name = os.path.basename(site_dir)
    #     # Filter images for each site
    #     filtered_images = filter_images(site_dir, start_time_str, end_time_str, start_year, end_year)
    #     print(f"Total photos: {filtered_images['total_photos']}")
    #     print(f"Start date: {filtered_images['start_date']}")
    #     print(f"End date: {filtered_images['end_date']}")
    #     print(f"Missing dates: {filtered_images['missing_dates']}")
    #
    #     output_dir = os.path.abspath('M:/Remote Cameras/Timelapses')
    #     output_file = create_timelapse(site_name, filtered_images, out_dir=output_dir, frame_rate=7, resize_percent=10, font_scale=1, line_type=2, position="BL")


    ##--------------------------- Example Usage------------------------------##
# parent_dir = os.path.abspath('M:\\Remote Cameras\\full_res')
# results = find_sandbar_dirs(parent_dir)
#
# valid_site_names = []
# for site in results['site_names']:
#     num_files = results['sandbar_info'][site]['number_of_files']
#     end_time = results['sandbar_info'][site]['end_date_time']
#     if num_files >= 1000 and end_time > datetime(2023, 1, 1, 12, 30): # skip sites with less than 1000 files and with records ending before 2019
#         valid_site_names.append(site)
#     else:
#         print(f'Site: {site} skipped because it contains just {num_files} image files or end date-time is {end_time}')
#
# # Subset the 'sandbar_info' to include only valid site names
# subset_sandbar_info = {site: results['sandbar_info'][site] for site in valid_site_names}
#
# # Create a new 'results' dictionary including only valid site names and their corresponding directories
# subset_results = {
#     'site_names': valid_site_names,
#     'sandbar_dirs': [dir for dir in results['sandbar_dirs'] if os.path.basename(dir) in valid_site_names],
#     'sandbar_info': subset_sandbar_info
# }
#
# print("Site Names:", subset_results['site_names'])
# print("Sandbar Directories:")
# pprint(subset_results['sandbar_dirs'])
# print("\nSandbar Information:")
# pprint(subset_results['sandbar_info'])
#
#
# '''
# Now lets loop through the subset of image directories and create timelapses for each of the sandbars
# as we do that we will filter images so we end up with just one image per day between 11am and 1pm
# '''
#
# start_time_str = '1100'
# end_time_str = '1300'
# start_year = 2014
# end_year = 2024
#
#
#
# for site_dir in subset_results['sandbar_dirs']:
#     site_name = os.path.basename(site_dir)
#     # Filter images for each site
#     filtered_images = filter_images(site_dir, start_time_str, end_time_str, start_year, end_year)
#     print(f"Total photos: {filtered_images['total_photos']}")
#     print(f"Start date: {filtered_images['start_date']}")
#     print(f"End date: {filtered_images['end_date']}")
#     print(f"Missing dates: {filtered_images['missing_dates']}")
#
#     output_dir = os.path.abspath('M:/Remote Cameras/Timelapses')
#     output_file = create_timelapse(site_name, filtered_images, out_dir=output_dir, frame_rate=7, resize_percent=10, font_scale=1, line_type=2, position="BL")
#
