import streamlit as st
import os
import google.generativeai as genai
from PIL import Image
import io
import pandas as pd
from datetime import datetime
import random
import requests
import json

# Configure page
st.set_page_config(page_title="EcoStyle: AI Wardrobe Buddy", page_icon="👔", layout="wide")

# Initialize Gemini API (you'll need to add your API key)
def initialize_gemini():
    api_key = st.secrets.get("GOOGLE_API_KEY", "")
    if not api_key:
        api_key = st.sidebar.text_input("Enter your Google API Key", type="password")
        if not api_key:
            st.warning("Please add your Google API key to continue")
            st.stop()
    
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-1.5-flash')

# Initialize session state variables if they don't exist
if 'wardrobe' not in st.session_state:
    st.session_state.wardrobe = []
if 'outfits' not in st.session_state:
    st.session_state.outfits = []
if 'weather' not in st.session_state:
    st.session_state.weather = {"temp": 68, "condition": "Clear"}

# Create sidebar menu
st.sidebar.title("EcoStyle Menu")
page = st.sidebar.radio(
    "Choose a feature:", 
    ["My Virtual Closet", "Daily Outfit Suggestions", "Sustainability Scores", "About"]
)

# Mock function to get weather
def get_weather(city="New York"):
    # In a real app, you'd connect to OpenWeatherMap or similar API
    conditions = ["Clear", "Cloudy", "Rainy", "Windy", "Snowy"]
    temp = random.randint(35, 85)
    condition = random.choice(conditions)
    
    st.session_state.weather = {"temp": temp, "condition": condition}
    return st.session_state.weather

# Function to generate clothing details with Gemini
def analyze_clothing_image(model, image):
    try:
        prompt = """
        You are a clothing analysis expert. For the image provided:
        1. Identify the type of clothing (e.g., shirt, pants, dress)
        2. Describe its color(s)
        3. Identify the material if visible (e.g., cotton, denim, polyester)
        4. Determine its style (casual, formal, sporty, etc.)
        5. Suggest seasons appropriate for this item (summer, winter, all-season, etc.)
        
        Format your response as a JSON object with these keys: 
        type, color, material, style, season, sustainability_score
        
        For sustainability_score, provide a score from 1-10 based on the likely material.
        Cotton: 6, Organic Cotton: 8, Polyester: 3, Recycled Polyester: 5, Nylon: 2, 
        Wool: 7, Linen: 9, Silk: 7, Denim: 4, Leather: 3, Vegan Leather: 4
        """
        
        response = model.generate_content([prompt, image])
        response_text = response.text
        
        # Extract JSON part from the response
        import re
        json_match = re.search(r'{.*}', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            item_details = json.loads(json_str)
            return item_details
        else:
            return {
                "type": "Unknown",
                "color": "Unknown",
                "material": "Unknown",
                "style": "Unknown",
                "season": "Unknown",
                "sustainability_score": 5
            }
           
    except Exception as e:
        st.error(f"Error analyzing image: {e}")
        return {
            "type": "Unknown",
            "color": "Unknown",
            "material": "Unknown",
            "style": "Unknown",
            "season": "Unknown",
            "sustainability_score": 5
        }

# Function to suggest outfits with Gemini
def get_outfit_suggestions(model, wardrobe, weather):
    if not wardrobe:
        return []
    
    # Create prompt with wardrobe items and weather
    wardrobe_text = ""
    for idx, item in enumerate(wardrobe):
        wardrobe_text += f"{idx+1}. {item['type']}: {item['color']} {item['material']}, {item['style']} style, suitable for {item['season']} season.\n"
    
    prompt = f"""
    As a fashion stylist, create 3 outfit combinations using these clothing items:
    
    {wardrobe_text}
    
    Current weather: {weather['temp']}°F, {weather['condition']}
    
    For each outfit:
    1. Select compatible items that would work well together
    2. Consider the current weather conditions
    3. Balance style and sustainability
    
    Format your response as a JSON array with 3 objects, each object having:
    - outfit_name: A catchy name for the outfit
    - items: Array of item indexes used (from the numbered list above)
    - description: Brief description of why these work together
    - occasion: Suggested occasion for this outfit
    - sustainability_score: Overall sustainability score (1-10)
    
    Return ONLY the JSON with no additional explanations.
    """
    
    try:
        response = model.generate_content(prompt)
        response_text = response.text
        
        # Extract JSON part from the response
        import re
        json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            outfits = json.loads(json_str)
            return outfits
        else:
            return []
            
    except Exception as e:
        st.error(f"Error generating outfits: {e}")
        return []

# Add clothing item function
def add_clothing_item(model):
    st.subheader("Add New Item to Your Wardrobe")
    
    uploaded_file = st.file_uploader("Upload a photo of your clothing item:", type=["jpg", "jpeg", "png"])
    
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.image(image, caption="Uploaded clothing item", width=300)
        
        with col2:
            with st.spinner("Analyzing your clothing item..."):
                # Convert PIL Image to format expected by Gemini
                img_byte_arr = io.BytesIO()
                image.save(img_byte_arr, format=image.format if image.format else 'JPEG')
                img_byte_arr = img_byte_arr.getvalue()
                
                # Create a Part object from the image bytes
                image_part = {"mime_type": f"image/{image.format.lower() if image.format else 'jpeg'}", "data": img_byte_arr}
                
                # Get analysis from Gemini
                item_details = analyze_clothing_image(model, image_part)
                
                # Display analysis results
                st.write("**Item Analysis Results:**")
                for key, value in item_details.items():
                    # Replace line 183 in the add_clothing_item function
                    if key == "sustainability_score":
                        # Extract just the numeric part of the value
                        try:
                            numeric_value = float(str(value).split()[0])  # Take first part before any space
                            st.progress(numeric_value / 10)
                            st.write(f"**{key.replace('_', ' ').title()}:** {value}/10")
                        except ValueError:
                            # Fallback if conversion fails
                            st.write(f"**{key.replace('_', ' ').title()}:** {value}")
                    
                
                # Add to wardrobe button
                if st.button("Add to My Wardrobe"):
                    # Add timestamp and ID
                    item_details["added_date"] = datetime.now().strftime("%Y-%m-%d")
                    item_details["id"] = len(st.session_state.wardrobe) + 1
                    
                    # Save image as base64 (in a real app, you'd save to storage)
                    img_byte_arr = io.BytesIO()
                    image.save(img_byte_arr, format=image.format if image.format else 'JPEG')
                    img_byte_arr = img_byte_arr.getvalue()
                    item_details["image"] = img_byte_arr
                    
                    # Add to wardrobe
                    st.session_state.wardrobe.append(item_details)
                    st.success("Item added to your wardrobe!")

# Display Virtual Closet function
def display_virtual_closet():
    st.header("My Virtual Closet")
    
    # Add new clothing item
    with st.expander("Add New Clothing Item", expanded=False):
        model = initialize_gemini()
        add_clothing_item(model)
    
    # Display wardrobe items
    if not st.session_state.wardrobe:
        st.info("Your wardrobe is empty. Add some items to get started!")
    else:
        st.subheader(f"You have {len(st.session_state.wardrobe)} items in your wardrobe")
        
        # Filter options
        col1, col2, col3 = st.columns(3)
        with col1:
            filter_type = st.selectbox("Filter by Type", ["All"] + list(set(item["type"] for item in st.session_state.wardrobe)))
        with col2:
            filter_style = st.selectbox("Filter by Style", ["All"] + list(set(item["style"] for item in st.session_state.wardrobe)))
        with col3:
            filter_season = st.selectbox("Filter by Season", ["All"] + list(set(item["season"] for item in st.session_state.wardrobe)))
        
        # Apply filters
        filtered_wardrobe = st.session_state.wardrobe
        if filter_type != "All":
            filtered_wardrobe = [item for item in filtered_wardrobe if item["type"] == filter_type]
        if filter_style != "All":
            filtered_wardrobe = [item for item in filtered_wardrobe if item["style"] == filter_style]
        if filter_season != "All":
            filtered_wardrobe = [item for item in filtered_wardrobe if item["season"] == filter_season]
        
        # Display wardrobe items in a grid
        cols = st.columns(4)
        for i, item in enumerate(filtered_wardrobe):
            with cols[i % 4]:
                try:
                    # Create image from bytes
                    img = Image.open(io.BytesIO(item["image"]))
                    st.image(img, caption=f"{item['color']} {item['type']}", width=150)
                    st.caption(f"Style: {item['style']} | Season: {item['season']}")
                    
                    # Show sustainability score with color
                    score = item["sustainability_score"]
                    score_color = "green" if score >= 7 else "orange" if score >= 4 else "red"
                    st.markdown(f"<span style='color:{score_color}'>Sustainability: {score}/10</span>", unsafe_allow_html=True)
                    
                    # Add a "Remove" button
                    if st.button(f"Remove Item #{item['id']}"):
                        st.session_state.wardrobe.remove(item)
                        st.experimental_rerun()
                except Exception as e:
                    st.error(f"Error displaying item: {e}")

# Display Outfit Suggestions function
def display_outfit_suggestions():
    st.header("Daily Outfit Suggestions")
    
    # Check if wardrobe has items
    if not st.session_state.wardrobe:
        st.info("Your wardrobe is empty. Add some items to get outfit suggestions!")
        return
    
    # Weather information
    col1, col2 = st.columns(2)
    with col1:
        city = st.text_input("Your Location", "New York")
    with col2:
        if st.button("Get Weather"):
            weather = get_weather(city)
            st.success(f"Weather updated: {weather['temp']}°F, {weather['condition']}")
    
    # Display current weather
    st.subheader("Current Weather")
    weather_col1, weather_col2 = st.columns(2)
    with weather_col1:
        st.metric("Temperature", f"{st.session_state.weather['temp']}°F")
    with weather_col2:
        st.write(f"Condition: {st.session_state.weather['condition']}")
    
    # Occasion selection
    occasion = st.selectbox(
        "What's the occasion today?",
        ["Casual Day", "Work/Office", "Formal Event", "Workout", "Date Night", "Weekend Outing"]
    )
    
    # Generate outfit suggestions
    if st.button("Generate Today's Outfits"):
        with st.spinner("Creating perfect outfits for you..."):
            model = initialize_gemini()
            outfits = get_outfit_suggestions(model, st.session_state.wardrobe, st.session_state.weather)
            st.session_state.outfits = outfits
    
    # Display outfit suggestions
    if st.session_state.outfits:
        st.subheader("Your Outfit Suggestions")
        
        for i, outfit in enumerate(st.session_state.outfits):
            with st.container():
                st.markdown(f"### {outfit['outfit_name']}")
                st.write(f"**Occasion:** {outfit['occasion']}")
                st.write(f"**Description:** {outfit['description']}")
                
                # Display sustainability score
                score = outfit.get('sustainability_score', 5)
                st.progress(int(score) / 10)
                st.write(f"Sustainability Score: {score}/10")
                
                # Display outfit items
                items_col = st.columns(len(outfit['items']))
                for j, item_idx in enumerate(outfit['items']):
                    try:
                        # Convert the index to integer and adjust for 0-indexing
                        item_idx = int(item_idx) - 1
                        if 0 <= item_idx < len(st.session_state.wardrobe):
                            item = st.session_state.wardrobe[item_idx]
                            with items_col[j]:
                                # Create image from bytes
                                img = Image.open(io.BytesIO(item["image"]))
                                st.image(img, caption=f"{item['color']} {item['type']}", width=100)
                    except Exception as e:
                        st.error(f"Error displaying outfit item: {e}")
                
                # Feedback buttons
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button(f"👍 Love this outfit! ({i+1})"):
                        st.success("Great! We'll recommend more like this.")
                with col2:
                    if st.button(f"👎 Not my style ({i+1})"):
                        st.info("Thanks for the feedback. We'll adjust our recommendations.")
                with col3:
                    if st.button(f"📋 Save outfit ({i+1})"):
                        st.success("Outfit saved to your favorites!")
                
                st.markdown("---")
def display_sustainability_scores():
    st.header("Sustainability Dashboard")
    
    if not st.session_state.wardrobe:
        st.info("Add items to your wardrobe to see sustainability insights.")
        return
    
    # Calculate sustainability metrics
    total_items = len(st.session_state.wardrobe)
    
    # Safely convert sustainability scores to numbers
    scores = []
    for item in st.session_state.wardrobe:
        try:
            # Extract just the numeric part of the score
            score_str = str(item["sustainability_score"]).split()[0]  # Take first part before any space
            score = float(score_str)
            scores.append(score)
        except (ValueError, TypeError):
            # Use a default value if conversion fails
            scores.append(5.0)
    
    total_score = sum(scores)
    avg_score = total_score / total_items if total_items > 0 else 0
    
    # Materials breakdown
    materials = {}
    for item in st.session_state.wardrobe:
        material = item["material"]
        if material in materials:
            materials[material] += 1
        else:
            materials[material] = 1
    
    # Display key metrics
    st.subheader("Your Sustainability Overview")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Wardrobe Size", total_items)
    with col2:
        st.metric("Average Sustainability", f"{avg_score:.1f}/10")
    with col3:
        sustainability_level = "High" if avg_score >= 7 else "Medium" if avg_score >= 5 else "Low"
        st.metric("Sustainability Level", sustainability_level)
    
    # Display materials breakdown
    st.subheader("Materials in Your Wardrobe")
    
    # Create dataframe for chart
    materials_df = pd.DataFrame({
        'Material': list(materials.keys()),
        'Count': list(materials.values())
    })
    
    # Display as bar chart
    st.bar_chart(materials_df.set_index('Material'))
    
    # Sustainability tips based on wardrobe
    st.subheader("Your Sustainable Fashion Tips")
    
    if avg_score < 5:
        st.warning("""
        Your wardrobe could be more sustainable. Consider:
        - Replacing synthetic materials with natural fibers
        - Looking for second-hand or vintage alternatives
        - Investing in fewer, higher-quality pieces
        """)
    elif avg_score < 7:
        st.info("""
        You're on the right track! To improve:
        - Try organic cotton instead of conventional
        - Look for recycled materials when buying synthetics
        - Consider how often you'll wear an item before purchasing
        """)
    else:
        st.success("""
        Great job! Your wardrobe is quite sustainable. Keep up by:
        - Taking good care of your items to extend their life
        - Sharing your sustainable fashion journey with friends
        - Supporting ethical brands when you do need to shop
        """)

# Display About page
def display_about():
    st.header("About EcoStyle: Your AI Wardrobe Buddy")
    
    st.markdown("""
    ## Making sustainable fashion simple and personal
    
    **EcoStyle** helps you:
    - Organize your wardrobe digitally
    - Get personalized outfit suggestions
    - Make more sustainable fashion choices
    - Shop smarter when you need new items
    
    ### How It Works
    1. **Snap & Organize:** Take pictures of your clothes and our AI sorts them
    2. **Morning Magic:** Get outfit ideas perfect for today's weather
    3. **Style Without Shopping:** Discover new combinations from what you already own
    4. **Green Guidance:** Find brands that match your values when shopping
    
    ### Technology
    Built with open-source tools:
    - **Google's Gemini-1.5-flash** for AI vision and suggestions
    - **Streamlit** for the user interface
    - **Python** for the backend processing
    
    ### Privacy
    - Your clothing photos stay private
    - We don't sell your style data to fashion brands
    
    ### Team
    Created with ❤️ by Quantum Leaf
    """)

# Main app logic
def main():
    # Display title and intro
    st.title("🌿 EcoStyle: Your AI Wardrobe Buddy")
    st.write("Making sustainable fashion simple and personal. Organize your wardrobe and get AI-powered style recommendations.")
    
    # Display the selected page
    if page == "My Virtual Closet":
        display_virtual_closet()
    elif page == "Daily Outfit Suggestions":
        display_outfit_suggestions()
    elif page == "Sustainability Scores":
        display_sustainability_scores()
    else:
        display_about()

if __name__ == "__main__":
    main()