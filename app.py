import streamlit as st
import pickle
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import google.generativeai as genai
import os
import re
from typing import List, Dict, Tuple, Optional

# --- Page Configuration (must be first Streamlit command) ---
st.set_page_config(
    page_title="Mr.Isuzu Sales Assistant", 
    layout="centered", 
    page_icon='⚙️'
)

# --- Cached Resource Loading ---
@st.cache_resource
def load_models_and_data():
    """Load FAISS index, metadata, and ML models (cached)"""
    try:
        index = faiss.read_index("car_index.bin")
        with open("car_metadata.pkl", "rb") as f:
            car_data = pickle.load(f)
        model_embed = SentenceTransformer("all-mpnet-base-v2")
        
        # Configure Gemini with secrets management
        api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            st.error("⚠️ GEMINI_API_KEY tidak ditemukan. Periksa konfigurasi secrets.")
            st.stop()
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")
        
        return index, car_data, model_embed, model
    except FileNotFoundError as e:
        st.error(f"❌ File tidak ditemukan: {e}")
        st.stop()
    except Exception as e:
        st.error(f"❌ Error loading resources: {e}")
        st.stop()

# Load resources once
index, car_data, model_embed, model = load_models_and_data()

# --- Helper Functions ---
def is_car_mentioned(car_name: str, question: str) -> bool:
    """Check if car name is mentioned in question"""
    # Normalize by removing spaces and dashes
    car_name_clean = car_name.lower().replace("-", "").replace(" ", "")
    question_clean = question.lower().replace("-", "").replace(" ", "")
    
    if car_name_clean in question_clean:
        return True
    
    # Token-based matching
    name_tokens = set(re.findall(r'\b\w+\b', car_name.lower()))
    question_tokens = set(re.findall(r'\b\w+\b', question.lower()))
    return bool(name_tokens & question_tokens)

def build_context(cars: List[Dict]) -> str:
    """Build context string from car data"""
    if not cars:
        return "Tidak ditemukan data teknis yang relevan untuk pertanyaan ini."
    
    context_parts = []
    for car in cars:
        perbedaan = "\n".join([f"- {k}: {v}" for k, v in car['perbedaan'].items()])
        context_parts.append(
            f"Mobil {car['nama']}:\n"
            f"Spesifikasi: {car['spesifikasi']}\n"
            f"Keunggulan: {car['keunggulan']}\n"
            f"Perbedaan:\n{perbedaan}\n"
            f"Link Brosur: {car['url brosur']}\n"
        )
    
    return "\n".join(context_parts)

def search_cars(user_input: str) -> Tuple[List[Dict], Optional[np.ndarray]]:
    """
    Search for relevant cars based on user input
    Returns: (selected_cars, similarity_scores)
    """
    question_lower = user_input.lower()
    
    # Try direct car name detection first
    detected_cars = [
        car for car in car_data 
        if is_car_mentioned(car['nama'], question_lower)
    ]
    
    if detected_cars:
        return detected_cars, None
    
    # Fallback to FAISS semantic search
    try:
        query_vec = model_embed.encode([user_input], normalize_embeddings=True)
        D, I = index.search(np.array(query_vec), k=1)
        
        # Configurable threshold
        SIMILARITY_THRESHOLD = 0.4
        
        if D[0][0] > SIMILARITY_THRESHOLD:
            return [car_data[I[0][0]]], D
        else:
            return [], D
            
    except Exception as e:
        st.error(f"❌ Error dalam pencarian: {e}")
        return [], None

def generate_response(user_input: str, context: str, car_list: str) -> str:
    """Generate AI response using Gemini"""
    prompt = f"""
Kamu adalah Mr.Isuzu, asisten AI ramah dan cerdas yang membantu pelanggan memahami dan membandingkan berbagai macam mobil Isuzu

Pertanyaan pengguna:
"{user_input}"

Context dari database produk:
{context}

Instruksi:
1. Jika pengguna bertanya mengenai jenis mobil apa saja yang dimiliki maka berikan list nama mobil berikut: {car_list}. Akhiri jawaban.
2. Jika pengguna meminta penjelasan tentang mobil, jelaskan spesifikasinya, keunggulannya, dan fitur unik dari data yang tersedia.
3. Jika pengguna menanyakan perbandingan antara mobil, gunakan bagian "Perbedaan" dari masing-masing mobil dan tampilkan dalam bentuk tabel.
4. Setelah tabel perbandingan, berikan ringkasan dalam bentuk paragraf: sampaikan poin-poin utama yang membedakan kedua mobil secara jelas.
5. Jika tidak ditemukan data yang cocok, sampaikan dengan sopan bahwa datanya belum tersedia dan hindari asumsi teknis yang tidak akurat.
6. Jika terdapat data dari context, persilakan pengguna untuk mengunduh brosur (sertakan 'Link Brosur' jika tersedia) dan melihat gambar dari mobil yang terdapat di sebelah kanan layar
7. Jika menyertakan link brosur, gunakan format markdown dengan teks yang jelas dan enak dibaca. Contoh: [Klik di sini untuk melihat brosur](URL)
   Hindari menampilkan URL mentah.

Tuliskan jawaban dalam bahasa Indonesia yang sopan, jelas, dan mudah dipahami. Hindari istilah teknis yang rumit kecuali diperlukan.
"""
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"⚠️ Maaf, terjadi kesalahan saat memproses jawaban: {str(e)}\n\nSilakan coba lagi."

# --- UI Components ---
st.title("🚘 Mr.Isuzu - Sales Assistant")
st.write("Tanyakan tentang spesifikasi, keunggulan, atau perbandingan mobil ISUZU yang tersedia.")

# User input
user_input = st.text_area("💬 Pertanyaan Anda tentang mobil:", height=75)

# Process query
if st.button("Tanyakan Sekarang", type="primary"):
    if not user_input.strip():
        st.warning("⚠️ Silakan masukkan pertanyaan terlebih dahulu.")
    else:
        with st.spinner("🔍 Mr.Isuzu sedang mencari jawaban..."):
            # Prepare car list
            car_names = [car['nama'].lower() for car in car_data]
            car_list = ", ".join(sorted(car_names))
            
            # Search for relevant cars
            selected_cars, similarity_scores = search_cars(user_input)
            
            # Build context
            context = build_context(selected_cars)
            
            # Generate AI response
            answer = generate_response(user_input, context, car_list)
        
        # Display results in two columns
        left, right = st.columns([2, 1])
        
        with left:
            st.markdown("### 💡 Jawaban Mr.Isuzu")
            st.success(answer)
        
        with right:
            if selected_cars:
                st.markdown("### 📌 Detail Mobil")
                
                for idx, car in enumerate(selected_cars):
                    st.markdown(f"**{car['nama']}**")
                    
                    # Show similarity score only if from FAISS search
                    if similarity_scores is not None and len(similarity_scores[0]) > idx:
                        score = similarity_scores[0][idx]
                        st.caption(f"Relevansi: {score:.2%}")
                    
                    # Display image
                    image_path = car.get("gambar")
                    if image_path and os.path.exists(image_path):
                        st.image(image_path, caption=car['nama'], use_container_width=True)
                    else:
                        st.info(f"📷 Gambar tidak tersedia")
                    
                    # Brochure download
                    brochure_path = car.get("brosur")
                    if brochure_path and os.path.exists(brochure_path):
                        with open(brochure_path, "rb") as pdf_file:
                            st.download_button(
                                label=f"📄 Unduh Brosur",
                                data=pdf_file,
                                file_name=os.path.basename(brochure_path),
                                mime="application/pdf",
                                key=f"brochure_{idx}"
                            )
                    else:
                        st.caption("📄 Brosur belum tersedia")
                    
                    if idx < len(selected_cars) - 1:
                        st.divider()
            else:
                st.info("💭 Tidak ada data mobil spesifik yang cocok dengan pertanyaan Anda.")

# Footer
st.markdown("---")
st.caption("🤖 Powered by Gemini AI & FAISS Vector Search")