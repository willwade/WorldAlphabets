document.addEventListener('DOMContentLoaded', () => {
    const languageList = document.getElementById('language-list');
    const languageDetails = document.getElementById('language-details');
    const modal = document.getElementById('modal');
    const modalLetter = document.getElementById('modal-letter');
    const modalCopyBtn = document.getElementById('modal-copy-btn');
    const modalClose = document.getElementById('modal-close');

    let languagesData = [];
    let translationsData = {};
    let languageToDriverMapping = {};

    // Event listeners for closing the modal
    modalClose.onclick = () => modal.style.display = 'none';
    window.onclick = (event) => {
        if (event.target == modal) {
            modal.style.display = 'none';
        }
    };

    // Load all data at once
    Promise.all([
        fetch('../data/index.json').then(res => res.json()),
        fetch('../data/translations.json').then(res => res.json()).catch(() => ({})),
        fetch('../data/mappings/language_to_driver.json').then(res => res.json()).catch(() => ({}))
    ])
    .then(([indexData, transData, driverMapping]) => {
        languagesData = indexData;
        translationsData = transData;
        languageToDriverMapping = driverMapping;

        languagesData.forEach(language => {
            const langDiv = document.createElement('div');
            langDiv.textContent = language['language-name'];
            langDiv.classList.add('language-item');
            langDiv.dataset.langCode = language.language;
            langDiv.addEventListener('click', () => showLanguageDetails(language.language));
            languageList.appendChild(langDiv);
        });
    });

    function renderKeyboard(layoutData) {
        const container = document.createElement('div');
        container.classList.add('keyboard');
        const key_unit = 20; // in pixels
        let max_x = 0;
        let max_y = 0;

        layoutData.keys.forEach(key => {
            if (!key.shape) return;

            const keyEl = document.createElement('div');
            keyEl.classList.add('key');
            keyEl.style.position = 'absolute';
            keyEl.style.left = `${key.shape.x * key_unit}px`;
            keyEl.style.top = `${key.shape.y * key_unit}px`;
            keyEl.style.width = `${key.shape.w * key_unit}px`;
            keyEl.style.height = `${key.shape.h * key_unit}px`;

            const legend = key.legends.base || '';
            keyEl.textContent = legend;

            container.appendChild(keyEl);

            if (key.shape.x + key.shape.w > max_x) max_x = key.shape.x + key.shape.w;
            if (key.shape.y + key.shape.h > max_y) max_y = key.shape.y + key.shape.h;
        });

        container.style.width = `${max_x * key_unit}px`;
        container.style.height = `${max_y * key_unit}px`;

        return container;
    }

    async function showLanguageDetails(langCode) {
        const language = languagesData.find(lang => lang.language === langCode);
        if (!language) return;

        languageDetails.innerHTML = 'Loading...';

        try {
            const alphabetResponse = await fetch(`../data/alphabets/${langCode}.json`);
            if (!alphabetResponse.ok) {
                languageDetails.innerHTML = `<p>Alphabet data for ${langCode} not found.</p>`;
                return;
            }
            const alphabetData = await alphabetResponse.json();

            languageDetails.innerHTML = '';

            const nameEl = document.createElement('h2');
            nameEl.textContent = language['language-name'];
            languageDetails.appendChild(nameEl);

            const directionEl = document.createElement('p');
            directionEl.textContent = `Direction: ${language.direction}`;
            languageDetails.appendChild(directionEl);

            const alphabetTitle = document.createElement('h3');
            alphabetTitle.textContent = 'Alphabet';
            languageDetails.appendChild(alphabetTitle);
            const alphabetList = document.createElement('div');
            alphabetList.classList.add('alphabet-list');
            if (alphabetData.alphabetical) {
                alphabetData.alphabetical.forEach(letter => {
                    const letterEl = document.createElement('span');
                    letterEl.textContent = letter;
                    letterEl.classList.add('letter');
                    letterEl.addEventListener('click', () => {
                        modalLetter.textContent = letter;
                        modal.style.display = 'flex';
                        modalCopyBtn.onclick = () => {
                            navigator.clipboard.writeText(letter).then(() => {
                                modalCopyBtn.textContent = 'Copied!';
                                setTimeout(() => modalCopyBtn.textContent = 'Copy', 1000);
                            }).catch(err => console.error('Could not copy text: ', err));
                        };
                    });
                    alphabetList.appendChild(letterEl);
                });
            }
            languageDetails.appendChild(alphabetList);

            const translation = translationsData[langCode];
            if (translation) {
                const translationTitle = document.createElement('h3');
                translationTitle.textContent = 'Example Phrase';
                languageDetails.appendChild(translationTitle);

                const translationEl = document.createElement('p');
                translationEl.textContent = `"${translation}"`;
                translationEl.style.fontStyle = 'italic';
                languageDetails.appendChild(translationEl);

                const audioUrl = `../audio/${langCode}.wav`;
                const audioResponse = await fetch(audioUrl);
                if (audioResponse.ok) {
                    const audioEl = new Audio(audioUrl);
                    const playButton = document.createElement('button');
                    playButton.textContent = '▶️ Play';
                    playButton.onclick = () => audioEl.play();
                    languageDetails.appendChild(playButton);
                }
            }

            const layoutName = languageToDriverMapping[langCode];
            if (layoutName) {
                const layoutResponse = await fetch(`../data/layouts/${layoutName}.json`);
                if (layoutResponse.ok) {
                    const layoutData = await layoutResponse.json();
                    const keyboardTitle = document.createElement('h3');
                    keyboardTitle.textContent = 'Keyboard Layout';
                    languageDetails.appendChild(keyboardTitle);
                    const keyboardContainer = renderKeyboard(layoutData);
                    languageDetails.appendChild(keyboardContainer);
                }
            }

            const linksTitle = document.createElement('h3');
            linksTitle.textContent = 'External Links';
            languageDetails.appendChild(linksTitle);

            const linksList = document.createElement('ul');
            const links = [
                { name: 'ISO 639-3', url: `https://iso639-3.sil.org/code/${langCode}` },
                { name: 'Ethnologue', url: `https://www.ethnologue.com/language/${langCode}` },
                { name: 'Glottolog', url: `http://glottolog.org/glottolog?iso=${langCode}` },
                { name: 'Wikipedia', url: `https://en.wikipedia.org/wiki/ISO_639:${langCode}` }
            ];

            links.forEach(linkInfo => {
                const listItem = document.createElement('li');
                const linkEl = document.createElement('a');
                linkEl.href = linkInfo.url;
                linkEl.textContent = linkInfo.name;
                linkEl.target = '_blank';
                listItem.appendChild(linkEl);
                linksList.appendChild(listItem);
            });
            languageDetails.appendChild(linksList);

        } catch (error) {
            console.error('Error loading language details:', error);
            languageDetails.innerHTML = `<p>Could not load language details.</p>`;
        }
    }
});
