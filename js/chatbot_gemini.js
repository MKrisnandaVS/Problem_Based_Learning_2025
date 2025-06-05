document.addEventListener("DOMContentLoaded", () => {
    const chatBox = document.getElementById("chatBox");
    const userInput = document.getElementById("userInput");
    const sendButton = document.getElementById("sendButton");

    // Ganti URL ini jika backend Anda berjalan di tempat lain
    const BACKEND_URL_GEMINI = "http://localhost:5000/gemini_chat";
    // const BACKEND_URL_COMPANY = "http://localhost:5000/company_info"; // Jika Anda ingin menambahkan logika khusus untuk ini

    function addMessage(text, sender) {
        const messageDiv = document.createElement("div");
        messageDiv.classList.add("chat-message", sender);
        messageDiv.textContent = text; // Gunakan textContent untuk keamanan dasar
        chatBox.appendChild(messageDiv);
        chatBox.scrollTop = chatBox.scrollHeight; // Auto-scroll ke bawah
    }

    async function sendMessageToBackend(message) {
        addMessage(message, "user"); // Tampilkan pesan pengguna
        userInput.value = ""; // Kosongkan input
        addMessage("Mengetik...", "bot"); // Tampilkan indikator loading

        try {
            // Kita akan selalu mengirim ke endpoint Gemini
            // Anda bisa menambahkan logika di sini jika ingin memilih endpoint
            // berdasarkan input (misal: jika ada kata 'info perusahaan', kirim ke /company_info)
            const response = await fetch(BACKEND_URL_GEMINI, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ message: message }),
            });

            // Hapus "Mengetik..."
            chatBox.removeChild(chatBox.lastChild);

            if (!response.ok) {
                const errorData = await response.json();
                addMessage(`Error: ${errorData.reply || 'Gagal terhubung ke backend'}`, "bot");
                return;
            }

            const data = await response.json();
            addMessage(data.reply, "bot"); // Tampilkan balasan bot

        } catch (error) {
             // Hapus "Mengetik..."
            if (chatBox.lastChild && chatBox.lastChild.textContent === "Mengetik...") {
                 chatBox.removeChild(chatBox.lastChild);
            }
            console.error("Fetch Error:", error);
            addMessage("Maaf, terjadi masalah koneksi. Coba lagi nanti.", "bot");
        }
    }

    sendButton.addEventListener("click", () => {
        const message = userInput.value.trim();
        if (message) {
            sendMessageToBackend(message);
        }
    });

    userInput.addEventListener("keypress", (event) => {
        if (event.key === "Enter") {
            const message = userInput.value.trim();
            if (message) {
                sendMessageToBackend(message);
            }
        }
    });
});