document.addEventListener('DOMContentLoaded', function() {
    fetchActivePolls();

    document.body.addEventListener('click', function(e) {
        if (e.target.matches('.poll-option')) {
            handleVote(e.target);
        }
    });
});

async function fetchActivePolls() {
    try {
        const response = await fetch('/polls/active');
        const polls = await response.json();
        displayPolls(polls);
    } catch (error) {
        console.error('Error fetching polls:', error);
    }
}

function displayPolls(polls) {
    const container = document.getElementById('active-polls');
    container.innerHTML = polls.map(poll => `
        <div class="poll-card card mb-3" data-poll-id="${poll.id}">
            <div class="card-body">
                <h5 class="card-title">${poll.title}</h5>
                <p class="card-text">${poll.description}</p>
                <div class="poll-options">
                    ${poll.options.map(option => `
                        <div class="poll-option" data-option-id="${option.id}">
                            ${option.text}
                        </div>
                    `).join('')}
                </div>
            </div>
        </div>
    `).join('');
}

async function handleVote(optionElement) {
    const pollId = optionElement.closest('.poll-card').dataset.pollId;
    const optionId = optionElement.dataset.optionId;

    try {
        const response = await fetch('/polls/vote', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                poll_id: pollId,
                option_id: optionId
            })
        });

        if (response.ok) {
            fetchActivePolls();
        }
    } catch (error) {
        console.error('Error submitting vote:', error);
    }
}
async function submitVote(pollId) {
    const pollContainer = document.querySelector(`[data-poll-id="${pollId}"]`);
    const selectedOptions = Array.from(pollContainer.querySelectorAll('input:checked'))
        .map(input => input.value);

    if (selectedOptions.length === 0) {
        alert('Будь ласка, виберіть варіант відповіді');
        return;
    }

    try {
        const response = await fetch('/vote', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                poll_id: pollId,
                option_ids: selectedOptions
            })
        });

        if (response.ok) {
            alert('Ваш голос враховано!');
            location.reload();
        } else {
            alert('Помилка при голосуванні');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Помилка при відправці голосу');
    }
}
async function submitVote(pollId) {
    try {
        const pollForm = document.querySelector(`[data-poll-id="${pollId}"]`);
        const selectedInputs = pollForm.querySelectorAll('input:checked');
        
        if (selectedInputs.length === 0) {
            alert('Будь ласка, виберіть варіант відповіді');
            return;
        }

        const selectedOptionIds = Array.from(selectedInputs).map(input => input.value);

        const response = await fetch('/vote', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                poll_id: pollId,
                option_ids: selectedOptionIds
            })
        });

        if (response.ok) {
            alert('Дякуємо за ваш голос!');
            window.location.reload(); 
        } else {
            const error = await response.json();
            alert(error.detail || 'Помилка при голосуванні');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Виникла помилка при спробі проголосувати');
    }
}
document.querySelectorAll('.poll-form').forEach(form => {
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const pollId = form.dataset.pollId;
        const selectedOption = form.querySelector('input[type="radio"]:checked');
        
        if (!selectedOption) {
            alert('Виберіть варіант відповіді');
            return;
        }
        
        try {
            const response = await fetch('/api/vote', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    poll_id: parseInt(pollId),
                    option_id: parseInt(selectedOption.value)
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                alert('Дякуємо за ваш голос!');
                location.reload();
            } else {
                alert(data.detail || 'Помилка при голосуванні');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Помилка при голосуванні');
        }
    });
});