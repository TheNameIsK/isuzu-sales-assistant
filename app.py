import streamlit as st
import pickle
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import google.generativeai as genai
from dotenv import load_dotenv
import os
import re

# --- Load environment & configure Gemini ---
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.0-flash")  # Or use gemini-1.5-pro if you want

# --- Load FAISS index and metadata ---
index = faiss.read_index("car_index.bin")
with open("car_metadata.pkl", "rb") as f:
    car_data = pickle.load(f)

# --- Load embedding model ---
model_embed = SentenceTransformer("all-MiniLM-L6-v2")

# --- Streamlit App Setup ---
st.set_page_config(page_title="Mr.Isuzu Sales Assistant", layout="centered", page_icon='⚙️')
st.title("🚘 Mr.Isuzu - Sales Assistant")
st.write("Tanyakan tentang spesifikasi, keunggulan, atau perbandingan mobil ISUZU yang tersedia.")

# --- User Input ---
user_input = st.text_area("💬 Pertanyaan Anda tentang mobil:", height=75)

# --- On Button Click ---
if st.button("Tanyakan Sekarang"):
    if not user_input.strip():
        st.warning("Silakan masukkan pertanyaan terlebih dahulu.")
    else:
        with st.spinner("Mr.Isuzu sedang mencari jawaban..."):

            question_lower = user_input.lower()
            car_names = [car['nama'].lower() for car in car_data]
            car_list = ", ".join(sorted(car_names))

            # --- Smart car name match using token-based partial matching and Regex ---
            # Used to try and get car names directly from user's input
            def is_car_mentioned(car_name, question):
                # Normalize car name and question by removing spaces and dashes
                car_name_clean = car_name.lower().replace("-", "").replace(" ", "")
                question_clean = question.lower().replace("-", "").replace(" ", "")
                if car_name_clean in question_clean:
                    return True

                # Fallback: token-based word boundary match using regex
                name_tokens = set(re.findall(r'\b\w+\b', car_name.lower()))
                question_tokens = set(re.findall(r'\b\w+\b', question.lower()))
                return bool(name_tokens & question_tokens)

            # Detect which cars (if any) were mentioned in the user's input
            detected_cars = [car for car in car_data if is_car_mentioned(car['nama'], question_lower)]

            # --- If car names are written in user's input, we fetch the right car data right away ---
            if detected_cars:
                selected_cars = detected_cars
                context = ""
                for car in selected_cars:
                    perbedaan = "\n".join([f"- {k}: {v}" for k, v in car['perbedaan'].items()])
                    context += f"""
                    Mobil {car['nama']}:
                    Spesifikasi: {car['spesifikasi']}
                    Keunggulan: {car['keunggulan']}
                    Perbedaan:\n{perbedaan}\n
                    Link Brosur: {car['url brosur']}
                    """
            else:
                # --- If there's no car name in user's input, we use FAISS to find the closest match ---
                query_vec = model_embed.encode([user_input], normalize_embeddings=True)
                D, I = index.search(np.array(query_vec), k=1)  # Only search for the single most similar entry

                selected_cars = []
                context = ""
                if D[0][0] > 0.4:
                    car = car_data[I[0][0]]
                    selected_cars.append(car)
                    perbedaan = "\n".join([f"- {k}: {v}" for k, v in car['perbedaan'].items()])
                    context += f"""
                        Mobil {car['nama']}:
                        Spesifikasi: {car['spesifikasi']}
                        Keunggulan: {car['keunggulan']}
                        Perbedaan:\n{perbedaan}\n
                        Link Brosur: [Klik di sini]({car['url brosur']})
                        """
            # --- Last fallback if no data is matched ---
            if not selected_cars:
                    context = "Tidak ditemukan data teknis yang relevan untuk pertanyaan ini."

            # --- Build Gemini Prompt ---
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

            response = model.generate_content(prompt)
            answer = response.text

        # --- Display Result ---
        left, right = st.columns([2, 1])

        with left:
            st.markdown("### 💡 Jawaban Mr.Isuzu")
            st.success(answer)

            # --- Show chosen car data ---
            with right:
                st.markdown("### ")
                if selected_cars:
                    st.markdown("### 📌 Detail Mobil yang Ditemukan")
                    for idx, car in enumerate(selected_cars):
                        st.markdown(f"**Nama:** {car['nama']}")

                        # --- Show score only if D is defined (FAISS was used) ---
                        if 'D' in locals() and len(D) > 0 and idx < len(D[0]):
                            st.markdown(f"**Skor Kecocokan:** `{D[0][idx]:.4f}`")

                    # --- Show car images ---
                    for idx, car in enumerate(selected_cars):
                        image_path = car.get("gambar")
                        if image_path and os.path.exists(image_path):
                            st.image(image_path, caption=car['nama'], use_container_width=True)
                        else:
                            st.info(f"Gambar untuk {car['nama']} tidak tersedia.")

                        # --- Show brochure download button ---
                        brochure_path = car.get("brosur")
                        if brochure_path and os.path.exists(brochure_path):
                            with open(brochure_path, "rb") as pdf_file:
                                st.download_button(
                                    label=f"📄 Unduh Brosur {car['nama']}",
                                    data=pdf_file,
                                    file_name=os.path.basename(brochure_path),
                                    mime="application/pdf"
                                )
                        else:
                            st.info(f"Brosur untuk {car['nama']} belum tersedia.")
                else:
                    st.info("Pertanyaan Anda belum cocok dengan data teknis yang tersedia.")
