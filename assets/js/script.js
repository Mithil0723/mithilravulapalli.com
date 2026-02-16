document.addEventListener('DOMContentLoaded', function () {

    // Typing animation
    const typingText = document.querySelector('.typing-text');
    if (typingText) {
        const texts = JSON.parse(typingText.getAttribute('data-texts'));
        let textIndex = 0;
        let charIndex = 0;

        function type() {
            if (charIndex < texts[textIndex].length) {
                typingText.textContent += texts[textIndex].charAt(charIndex);
                charIndex++;
                setTimeout(type, 100);
            } else {
                setTimeout(erase, 2000);
            }
        }

        function erase() {
            if (charIndex > 0) {
                typingText.textContent = texts[textIndex].substring(0, charIndex - 1);
                charIndex--;
                setTimeout(erase, 50);
            } else {
                textIndex = (textIndex + 1) % texts.length;
                setTimeout(type, 500);
            }
        }

        type();
    }

    // Video control
    const video = document.querySelector('.hero-video');
    const videoControl = document.querySelector('.video-control');
    if (video && videoControl) {
        let isPlaying = true;
        videoControl.addEventListener('click', function () {
            if (isPlaying) {
                video.pause();
                videoControl.textContent = '▶';
                videoControl.setAttribute('aria-label', 'Play background video');
            } else {
                video.play();
                videoControl.textContent = '⏸';
                videoControl.setAttribute('aria-label', 'Pause background video');
            }
            isPlaying = !isPlaying;
        });
    }

    // Intersection Observer for video performance
    const heroSection = document.querySelector('.hero-section');
    if (video && heroSection) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    video.play();
                } else {
                    video.pause();
                }
            });
        }, { threshold: 0.5 });
        observer.observe(heroSection);
    }

    // Sticky header
    const header = document.querySelector('.header');
    if (header) {
        window.addEventListener('scroll', function () {
            if (window.scrollY > 50) {
                header.classList.add('scrolled');
            } else {
                header.classList.remove('scrolled');
            }
        });
    }

    // Hamburger menu
    const hamburger = document.querySelector('.hamburger');
    const navMenu = document.querySelector('.nav-menu');
    if (hamburger && navMenu) {
        hamburger.addEventListener('click', () => {
            hamburger.classList.toggle('active');
            navMenu.classList.toggle('active');
        });

        document.querySelectorAll('.nav-link').forEach(n => n.addEventListener('click', () => {
            hamburger.classList.remove('active');
            navMenu.classList.remove('active');
        }));
    }

    // Project filter
    const filterBtns = document.querySelectorAll('.filter-btn');
    const projectCards = document.querySelectorAll('.project-card');

    if (filterBtns.length > 0 && projectCards.length > 0) {
        filterBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                // Set active button
                filterBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');

                const filter = btn.getAttribute('data-filter');

                // Show/hide projects
                projectCards.forEach(card => {
                    if (filter === 'all' || card.getAttribute('data-category') === filter) {
                        card.style.display = 'block';
                    } else {
                        card.style.display = 'none';
                    }
                });
            });
        });
    }

    /*-----------------------------------*\
     * #CHATBOT
    \*-----------------------------------*/

    // Backend URL — change this to your deployed URL for production
    const API_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' || window.location.hostname === ''
        ? 'http://localhost:8000'
        : 'https://your-backend.onrender.com'; // TODO: replace with your production URL

    const chatbotToggle = document.getElementById('chatbot-toggle');
    const chatbotContainer = document.getElementById('chatbot-container');
    const closeChatBtn = document.getElementById('close-chat-btn');
    const chatInput = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-btn');
    const chatMessages = document.getElementById('chat-messages');

    if (chatbotToggle && chatbotContainer && closeChatBtn && chatInput && sendBtn && chatMessages) {
        function toggleChat() {
            chatbotContainer.classList.toggle('active');
            const isActive = chatbotContainer.classList.contains('active');

            // Toggle icon
            const icon = chatbotToggle.querySelector('.toggle-icon');
            const closeIcon = chatbotToggle.querySelector('.toggle-icon-close');

            if (isActive) {
                icon.style.display = 'none';
                closeIcon.style.display = 'block';
                setTimeout(() => chatInput.focus(), 300);
            } else {
                icon.style.display = 'block';
                closeIcon.style.display = 'none';
            }
        }

        chatbotToggle.addEventListener('click', toggleChat);
        closeChatBtn.addEventListener('click', toggleChat);

        function addMessage(text, isUser = false) {
            const messageDiv = document.createElement('div');
            messageDiv.classList.add('message');
            messageDiv.classList.add(isUser ? 'user-message' : 'bot-message');

            const contentDiv = document.createElement('div');
            contentDiv.classList.add('message-content');
            contentDiv.textContent = text;

            messageDiv.appendChild(contentDiv);
            chatMessages.appendChild(messageDiv);

            // Auto scroll to bottom
            chatMessages.scrollTop = chatMessages.scrollHeight;
            return messageDiv;
        }

        async function handleUserMessage() {
            const text = chatInput.value.trim();
            if (!text) return;

            addMessage(text, true);
            chatInput.value = '';

            // Disable input while waiting
            chatInput.disabled = true;
            sendBtn.disabled = true;

            // Show loading message
            const loadingMsg = addMessage('Thinking...', false);

            try {
                const response = await fetch(`${API_URL}/chat`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: text })
                });

                if (!response.ok) {
                    throw new Error(`Server error: ${response.status}`);
                }

                const data = await response.json();
                // Replace loading message with actual reply
                loadingMsg.querySelector('.message-content').textContent = data.reply;

            } catch (error) {
                console.error('Chat error:', error);
                loadingMsg.querySelector('.message-content').textContent =
                    'Sorry, I couldn\'t connect to the server. Please try again later.';
            } finally {
                // Re-enable input
                chatInput.disabled = false;
                sendBtn.disabled = false;
                chatInput.focus();
            }
        }

        sendBtn.addEventListener('click', handleUserMessage);
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                handleUserMessage();
            }
        });
    }
});