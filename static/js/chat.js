document.addEventListener("DOMContentLoaded", function () {
    const chatForm = document.getElementById("chat-form");
    const queryInput = document.getElementById("query-input");
    const chatBox = document.getElementById("chat-box");

    // Debugging message to ensure the page has loaded and event listeners are attached
    console.log("Chat.js loaded, event listeners attached.");

    // Function to append a message to the chat box
    function appendMessage(role, content) {
        const messageElement = document.createElement("div");
        messageElement.classList.add("chat-message");

        const roleElement = document.createElement("div");
        roleElement.classList.add(role === "user" ? "user-message" : "bot-response");
        roleElement.innerHTML = `<strong>${role === "user" ? "You" : "EGPT"}:</strong> ${content}`;

        messageElement.appendChild(roleElement);
        chatBox.appendChild(messageElement);
        chatBox.scrollTop = chatBox.scrollHeight; // Auto-scroll to the bottom
    }

    // Handle form submission
    chatForm.addEventListener("submit", function (event) {
        event.preventDefault();
        const query = queryInput.value.trim();

        // Debug message for submitted query
        console.log("Form submitted with query:", query);

        if (query === "") {
            console.log("Empty query submitted, ignoring."); // Debug message for empty query
            return;
        }

        // Append user message to chat box
        appendMessage("user", query);
        queryInput.value = "";

        // Send query to the server
        fetch("/search", {
            method: "POST",
            body: new URLSearchParams({ query: query })
        })
            .then(response => {
                // Check if the response is OK
                if (!response.ok) {
                    console.error("Server returned an error:", response.status);
                    throw new Error("Server returned an error.");
                }
                return response.json();
            })
            .then(data => {
                console.log("Response data received from server:", data); // Debug message for response data

                // Display the AI response
                if (data.ai_response) {
                    appendMessage("bot", data.ai_response);
                }

                // Display the embedded PDF (if any)
                if (data.pdf_embed_url) {
                    const pdfEmbedHTML = `
                        <div class="pdf-display" style="border: 1px solid #ddd; margin-top: 10px; padding: 5px; height: 400px; overflow-y: auto;">
                            <iframe src="${data.pdf_embed_url}" width="100%" height="100%" type="application/pdf">
                                Your browser does not support PDFs. Please download the PDF to view it:
                                <a href="${data.pdf_embed_url}">Download PDF</a>.
                            </iframe>
                        </div>
                    `;
                    appendMessage("bot", pdfEmbedHTML);
                    console.log("PDF embedded successfully."); // Debug message for PDF embed
                } else {
                    console.log("No PDF to display for this query."); // Debug message if no PDF
                }

                // Display the embedded website (if any)
                if (data.embedded_website) {
                    const websiteEmbedHTML = `
                        <div class="embedded-website" style="border: 1px solid #ddd; margin-top: 10px; padding: 5px; height: 400px; overflow-y: auto;">
                            <iframe src="${data.embedded_website}" width="100%" height="100%">
                                Your browser does not support embedded websites.
                            </iframe>
                        </div>
                    `;
                    appendMessage("bot", websiteEmbedHTML);
                    console.log("Website embedded successfully."); // Debug message for website embed
                } else {
                    console.log("No website to display for this query."); // Debug message if no website
                }
            })
            .catch(error => {
                console.error("Error during fetch:", error);
                appendMessage("bot", "There was an error processing your request. Please try again later.");
            });
    });
});
