const scopeSelect = document.querySelector('select[name="scope"]');
const donorLabel = document.querySelector('label[for="donor_id"]');
const donorSelect = document.querySelector('select[name="donor_id"]');
const recipientLabel = document.querySelector('label[for="recipient_id"]');
const recipientSelect = document.querySelector('select[name="recipient_id"]');
const actionSelect = document.querySelector('select[name="action"]');
const replaceWithLabel = document.querySelector('label[for="replace_with"]');
const replaceWithInput = document.querySelector('input[name="replace_with"]');


function handleVisibility() {
    const selectedScope = scopeSelect.value;
    const selectedAction = actionSelect.value;

    donorLabel.style.display = selectedScope === 'DONOR' ? 'block' : 'none';
    donorSelect.style.display = selectedScope === 'DONOR' ? 'block' : 'none';
    recipientLabel.style.display = selectedScope === 'RECIPIENT' ? 'block' : 'none';
    recipientSelect.style.display = selectedScope === 'RECIPIENT' ? 'block' : 'none';

    replaceWithLabel.style.display = selectedAction === 'REPLACE' ? 'block' : 'none';
    replaceWithInput.style.display = selectedAction === 'REPLACE' ? 'block' : 'none';

    donorSelect.value = '';
    recipientSelect.value = '';
    replaceWithInput.value = '';
}

handleVisibility();

scopeSelect.addEventListener('change', handleVisibility);
actionSelect.addEventListener('change', handleVisibility);
