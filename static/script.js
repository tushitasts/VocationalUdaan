// document.addEventListener('DOMContentLoaded', function() {
//     // Check if the user is already logged in (use relative path)
//     fetch('/check_auth', { credentials: 'include' })
//         .then(res => res.json())
//         .then(data => {
//             if (data.is_authenticated) {
//                 // redirect to /search (server serves this route)
//                 window.location.href = '/search';
//             }
//         })
//         .catch(err => {
//             // ignore network error on initial check
//             console.warn('check_auth failed', err);
//         });

//     const loginForm = document.getElementById('login-form');
//     const signupForm = document.getElementById('signup-form');
//     const showSignupLink = document.getElementById('show-signup-link');
//     const showLoginLink = document.getElementById('show-login-link');
//     const loginContainer = document.getElementById('login-form-container');
//     const signupContainer = document.getElementById('signup-form-container');
//     const messageContainer = document.getElementById('message-container');

//     // Toggle forms
//     showSignupLink.addEventListener('click', (e) => {
//         e.preventDefault();
//         loginContainer.style.display = 'none';
//         signupContainer.style.display = 'block';
//         messageContainer.innerHTML = '';
//     });

//     showLoginLink.addEventListener('click', (e) => {
//         e.preventDefault();
//         signupContainer.style.display = 'none';
//         loginContainer.style.display = 'block';
//         messageContainer.innerHTML = '';
//     });

//     // Login submission (AJAX)
//     loginForm.addEventListener('submit', function(event) {
//         event.preventDefault();
//         const email = document.getElementById('login-email').value.trim();
//         const password = document.getElementById('login-password').value;

//         if (!email || !password) {
//             messageContainer.innerHTML = `<p class="error-message">Please enter email and password.</p>`;
//             return;
//         }

//         fetch('/login', {
//             method: 'POST',
//             headers: { 'Content-Type': 'application/json' },
//             credentials: 'include',
//             body: JSON.stringify({ email: email, password: password })
//         })
//         .then(handleAuthResponse)
//         .catch(err => {
//             messageContainer.innerHTML = `<p class="error-message">Network error. Try again.</p>`;
//             console.error(err);
//         });
//     });

//     // Signup submission (AJAX)
//     signupForm.addEventListener('submit', function(event) {
//         event.preventDefault();
//         const name = document.getElementById('signup-name').value.trim();
//         const email = document.getElementById('signup-email').value.trim();
//         const phone_number = document.getElementById('signup-phone').value.trim();
//         const password = document.getElementById('signup-password').value;
//         const education = document.getElementById('education').value;

//         if (!name || !email || !phone_number || !password) {
//             messageContainer.innerHTML = `<p class="error-message">Please fill all required fields.</p>`;
//             return;
//         }

//         const userData = { name, email, phone_number, password, education };

//         fetch('/signup', {
//             method: 'POST',
//             headers: { 'Content-Type': 'application/json' },
//             credentials: 'include',
//             body: JSON.stringify(userData)
//         })
//         .then(handleAuthResponse)
//         .catch(err => {
//             messageContainer.innerHTML = `<p class="error-message">Network error. Try again.</p>`;
//             console.error(err);
//         });
//     });

//     // Handles server response for login/signup
//     function handleAuthResponse(response) {
//         // first try parse JSON safely
//         response.json().then(data => {
//             if (response.ok) {
//                 // success => redirect to search
//                 messageContainer.innerHTML = `<p class="success-message">${data.message || 'Success. Redirecting...'}</p>`;
//                 setTimeout(() => {
//                     window.location.href = '/search';
//                 }, 700);
//             } else {
//                 // server returned an error payload
//                 const errMsg = data && (data.error || data.message) ? (data.error || data.message) : 'Authentication failed';
//                 messageContainer.innerHTML = `<p class="error-message">${errMsg}</p>`;
//             }
//         }).catch(() => {
//             // if JSON parse fails, use status text
//             if (response.ok) {
//                 window.location.href = '/search';
//             } else {
//                 messageContainer.innerHTML = `<p class="error-message">Unexpected server response (status ${response.status}).</p>`;
//             }
//         });
//     }
// });

// static/script.js (login/index page) - updated to support ?noredirect=1
document.addEventListener('DOMContentLoaded', function() {
    // Check for explicit query param to prevent auto-redirect (used when user clicks "Login / Sign Up" from search)
    const params = new URLSearchParams(window.location.search);
    const noRedirect = params.get('noredirect') === '1';

    // Check if the user is already logged in (use relative path)
    fetch('/check_auth', { credentials: 'include' })
        .then(res => res.json())
        .then(data => {
            // Only redirect automatically if authenticated AND caller did not request no-redirect
            if (data.is_authenticated && !noRedirect) {
                window.location.href = '/search';
            }
        })
        .catch(err => {
            // ignore network error on initial check
            console.warn('check_auth failed', err);
        });

    // --- grab elements if present (guard in case we render a different view) ---
    const loginForm = document.getElementById('login-form');
    const signupForm = document.getElementById('signup-form');
    const showSignupLink = document.getElementById('show-signup-link');
    const showLoginLink = document.getElementById('show-login-link');
    const loginContainer = document.getElementById('login-form-container');
    const signupContainer = document.getElementById('signup-form-container');
    const messageContainer = document.getElementById('message-container');

    // Toggle forms (only attach listeners if those elements exist)
    if (showSignupLink && loginContainer && signupContainer) {
        showSignupLink.addEventListener('click', (e) => {
            e.preventDefault();
            loginContainer.style.display = 'none';
            signupContainer.style.display = 'block';
            if (messageContainer) messageContainer.innerHTML = '';
        });
    }

    if (showLoginLink && loginContainer && signupContainer) {
        showLoginLink.addEventListener('click', (e) => {
            e.preventDefault();
            signupContainer.style.display = 'none';
            loginContainer.style.display = 'block';
            if (messageContainer) messageContainer.innerHTML = '';
        });
    }

    // Login submission (AJAX) - only if login form exists
    if (loginForm) {
        loginForm.addEventListener('submit', function(event) {
            event.preventDefault();
            const emailEl = document.getElementById('login-email');
            const passwordEl = document.getElementById('login-password');
            const email = emailEl ? emailEl.value.trim() : '';
            const password = passwordEl ? passwordEl.value : '';

            if (!email || !password) {
                if (messageContainer) messageContainer.innerHTML = `<p class="error-message">Please enter email and password.</p>`;
                return;
            }

            fetch('/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ email: email, password: password })
            })
            .then(handleAuthResponse)
            .catch(err => {
                if (messageContainer) messageContainer.innerHTML = `<p class="error-message">Network error. Try again.</p>`;
                console.error(err);
            });
        });
    }

    // Signup submission (AJAX) - only if signup form exists
    if (signupForm) {
        signupForm.addEventListener('submit', function(event) {
            event.preventDefault();
            const name = (document.getElementById('signup-name') || {}).value || '';
            const email = (document.getElementById('signup-email') || {}).value || '';
            const phone_number = (document.getElementById('signup-phone') || {}).value || '';
            const password = (document.getElementById('signup-password') || {}).value || '';
            const education = (document.getElementById('education') || {}).value || '';

            if (!name || !email || !phone_number || !password) {
                if (messageContainer) messageContainer.innerHTML = `<p class="error-message">Please fill all required fields.</p>`;
                return;
            }

            const userData = { name, email, phone_number, password, education };

            fetch('/signup', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify(userData)
            })
            .then(handleAuthResponse)
            .catch(err => {
                if (messageContainer) messageContainer.innerHTML = `<p class="error-message">Network error. Try again.</p>`;
                console.error(err);
            });
        });
    }

    // Handles server response for login/signup
    function handleAuthResponse(response) {
        response.json().then(data => {
            if (response.ok) {
                // prefer a server-supplied redirect if present, otherwise default to /search
                const redirectTo = (data && data.redirect) ? data.redirect : '/search';
                if (messageContainer) {
                    messageContainer.innerHTML = `<p class="success-message">${data.message || 'Success. Redirecting...'}</p>`;
                }
                setTimeout(() => {
                    window.location.href = redirectTo;
                }, 600);
            } else {
                const errMsg = data && (data.error || data.message) ? (data.error || data.message) : 'Authentication failed';
                if (messageContainer) messageContainer.innerHTML = `<p class="error-message">${errMsg}</p>`;
            }
        }).catch(() => {
            // fallback if JSON parse fails
            if (response.ok) {
                window.location.href = '/search';
            } else {
                if (messageContainer) messageContainer.innerHTML = `<p class="error-message">Unexpected server response (status ${response.status}).</p>`;
            }
        });
    }
});

