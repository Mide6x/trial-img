import streamlit as st
import pandas as pd
import re
import base64
import io
import requests
import cloudinary
import cloudinary.uploader
from cloudinary.utils import cloudinary_url

# Configuration for Cloudinary
cloudinary.config(
    
)

category_data = {
    "Beverages & Milk": ["Cocoa Beverages", "Everyday Tea", "Coffee", "Herbal Teas", "Milk"],
    "Breakfast & Cereals": ["Oats & Instant Cereals", "Sugar, Honey & Sweeteners", "Butter, Cheese & Other Spreads"],
    "Cooking Paste, Oil & Spices": ["Tomato Paste", "Cooking Oils", "Salt & Seasoning Cubes", "Herbs & Spices"],
    "Foodstuff": ["Grains & Rice", "Pasta & Noodles", "Poundo, Wheat & Semolina", "Canned Foods"],
    "Snacks & Confectioneries": ["Biscuits, Chin Chin & Cookies", "Nuts & Seeds", "Chocolates & Sweets", "Dry Fruits"],
    "Baking Ingredients": ["Flour & Baking Powder", "Baking Tools & Accessories"],
    "Alcoholic Drinks": ["Beer", "Liquers & Creams", "Cognac & Spirits", "Wines & Champagne"],
    "Non-Alcoholic Drinks": ["Fizzy Drinks & Malt", "Energy Drinks", "Wines", "Fruit Juices & Yoghurt", "Water"],
    "Baby & Kids": ["Diapering", "Baby & Toddler Health", "Daily Care", "Feeding & Nursing", "Toys & Gears", "School Bag"],
    "Detergent & Laundry Supplies": ["Bar Soaps & Detergents", "Bathroom & Toilet Cleaners", "Fabric Softeners", "Dish Washers", "Glass Cleaner", "Disinfectant & Sprays"],
    "Home Care & Household Supplies": ["Paper Towels & Serviettes", "Foil Paper & Cling Film", "Pests & Insect Control", "Lighters and Match Box", "Air Fresheners"],
    "Beauty & Personal Care": ["Skin Care", "Oral Care", "Hair Care", "Fragrances", "Feminine Care", "Men's Grooming", "Make-up", "Male Shoe", "Female Shoe"]
}

def convert_variant_format(variant):
    variant = str(variant)
    
    # Normalize input by replacing '×' with 'x', 'ltr' with 'L', and removing spaces around 'x'
    variant = re.sub(r'\s*[xX×]\s*', 'x', variant.replace('ltr', 'L'))
    
    # Patterns to match various formats with dynamic units
    pattern1 = re.compile(r'(\d+)\s*([a-zA-Z]+)\s*x\s*(\d+)', re.IGNORECASE)
    pattern2 = re.compile(r'(\d+)\s*x\s*(\d+)\s*([a-zA-Z]+)', re.IGNORECASE)
    pattern3 = re.compile(r'(\d+)x(\d+)([a-zA-Z]+)', re.IGNORECASE)
    
    # Try to match each pattern and convert to "sizeUNIT x number"
    match1 = pattern1.match(variant)
    if match1:
        size, unit, count = match1.groups()
        return f"{size.upper()}{unit.upper()} x {count}"
    
    match2 = pattern2.match(variant)
    if match2:
        count, size, unit = match2.groups()
        return f"{size.upper()}{unit.upper()} x {count}"
    
    match3 = pattern3.match(variant)
    if match3:
        count, size, unit = match3.groups()
        return f"{size.upper()}{unit.upper()} x {count}"
    
    return variant

def extract_size(weight_str):
    try:
        # Use regular expression to match a number followed by "kg", "G", or "ml"
        match = re.search(r"(\d+\.?\d*)(KG|G|ML|L|CL)", weight_str)
        if match:
            value = float(match.group(1))  # Extract the numeric part
            unit = match.group(2)
            if unit == "KG":
                return value * 1000  # Convert kg to grams
            elif unit == "G":
                return value
            elif unit == "ML":
                return value * 1  # Convert ml to grams (assuming density of 1 g/ml)
            elif unit == "L":
                return value * 1000 #Converting Litre to grams
            elif unit == "CL":
                return value * 10 #Converting CentiLitre to grams
        return None  # Handle cases where no unit or invalid format is found
    except:
        return None  # Handle other potential errors during conversion
    
def extract_amount(weight_str):
    try:
        amount_start = weight_str.find("x")
        if amount_start == -1:
            amount_start = weight_str.find("×")
        if amount_start == -1:
             amount_start = weight_str.find("X")
        if amount_start == -1:
            return None
        return int(weight_str[amount_start + 1:])
    except:
        return None

def categorize_product(product_name, manufacturer):
    tokens = product_name.lower().split()
    manufacturer = manufacturer.lower()
    
    for token in tokens:
        if 'poundo' in token or 'iyan' in token:
            return 'Poundo, Wheat & Semolina'
        elif 'rum' in token or 'liqueur' in token:
            return 'Liquers & Creams'
        elif 'soda' in token or 'bicarbonate' in token:
            return 'Baking Tools & Accessories'
        elif 'custard' in token:
            return 'Oats & Instant Cereals'
        elif 'sauce' in token:
            return 'Cooking Oils'
        
    if 'the coca-cola company' in manufacturer:
        return 'Fizzy Drinks & Malt'
    elif 'mount gay barbados' in manufacturer:
        return 'Liquers & Creams'
    
    for category, product_types in category_data.items():
        for product_type in product_types:
            for token in tokens:
                if token in product_type.lower():
                    return product_type
    
    return None
    
# Function to download an image from a URL
def download_image(url, save_path):
    try:
        # Send a GET request to the URL
        response = requests.get(url)
        
        # Check if the request was successful
        if response.status_code == 200:
            # Open the save path in write-binary mode and write the content to the file
            with open(save_path, 'wb') as file:
                file.write(response.content)
            st.write(f"Image successfully downloaded and saved to {save_path}")
        else:
            st.write(f"Failed to retrieve image. Status code: {response.status_code}")
    except Exception as e:
        st.error(f"An error occurred: {e}")

# Function to upload an image to Cloudinary and apply transformations
def upload_and_transform_image(image_url, Amount):
    try:
        # Upload the image to Cloudinary
        upload_result = cloudinary.uploader.upload(image_url)
        
        # Get the public ID of the uploaded image
        public_id = upload_result["public_id"]
        
        # Apply transformations
        transformed_url = cloudinary.CloudinaryImage(public_id).image(transformation=[
            {'background': "#FFFFFF", 'gravity': "center", 'height': 700, 'width': 1370, 'crop': "pad"},
            {'color': "#FFFFFF", 'overlay': {'font_family': "georgia", 'font_size': 71, 'font_weight': "bold", 'text_align': "left", 'text': f"X{Amount}"}},
            {'background': "#00350C"},
            {'flags': "layer_apply", 'gravity': "east", 'x': "0.2"}
        ])

        return transformed_url
    except Exception as e:
        st.error(f"An error occurred while uploading and transforming image: {e}")

# Function to process images in the DataFrame
def process_images(df):
    try:
        for index, row in df.iterrows():
            image_url = row['Image URL 1']
            Amount = extract_amount(row['Variant'])
            
            # Download image
            download_path = f"downloaded_image_{index}.jpg"
            download_image(image_url, download_path)
            
            # Upload to Cloudinary and get transformed URL
            transformed_image_url = upload_and_transform_image(download_path, Amount)
            
            # Update DataFrame with transformed URL
            df.at[index, 'Image URL 1'] = transformed_image_url
            
            # Delete downloaded image (optional)
            import os
            os.remove(download_path)
        
        st.success("Image processing completed successfully.")
    except Exception as e:
        st.error(f"An error occurred during image processing: {e}")

def clean_data(df):
    df['Product Category'] = df.apply(lambda row: categorize_product(row['Product Name'], row['Manufacturer Name']), axis=1)
    df['Variant'] = df['Variant'].apply(convert_variant_format)
    df['Variant Type'] = "Size"
    df['Weight'] = df['Variant'].apply(extract_size)
    df['Amount'] = df['Variant'].apply(extract_amount)
    df['Weight'] = round(((df['Weight'] * df['Amount']) / 1000) + 1)
    df['Product Name'] = df['Product Name'].str.title()
    return df

def main():
    st.title('Excel Data Cleaner')

    uploaded_file = st.file_uploader("Upload an Excel file", type=["xlsx", "xls"])

    if uploaded_file is not None:
        try:
            df = pd.read_excel(uploaded_file)
            st.write("Original Data:")
            st.write(df.head(12))

            cleaned_df = clean_data(df)

            # Process images
            process_images(cleaned_df)
            st.write("Cleaned Data:")
            st.write(cleaned_df.head(12))

            st.markdown(get_table_download_link(cleaned_df), unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Error: {e}")

def get_table_download_link(df):
    # Convert DataFrame to Excel file and download
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, sheet_name='cleaned_data', index=False)
    writer.save()
    excel_file = output.getvalue()
    b64 = base64.b64encode(excel_file).decode()
    href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="cleaned_data.xlsx">Download cleaned data XLSX file</a>'
    return href

if __name__ == '__main__':
    main()
