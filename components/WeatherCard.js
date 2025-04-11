// Weather condition mapping
const weatherConditions = {
    sunny: {
        borderBgClasses: 'border-yellow-400 bg-yellow-100/20',
        icon: `<svg class="w-12 h-12 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
              </svg>`,
        tagline: "Sun's out—time to code under the open sky!"
    },
    cloudy: {
        borderBgClasses: 'border-gray-400 bg-gray-100/20',
        icon: `<svg class="w-12 h-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z" />
              </svg>`,
        tagline: "Cloudy skies, bright ideas—let's get to work."
    },
    rain: {
        borderBgClasses: 'border-blue-400 bg-blue-100/20',
        icon: `<svg class="w-12 h-12 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z" />
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 15v2m4-2v2m4-2v2" />
              </svg>`,
        tagline: "Don't forget your umbrella—stay dry (and inspired)."
    },
    snow: {
        borderBgClasses: 'border-teal-400 bg-teal-100/20',
        icon: `<svg class="w-12 h-12 text-teal-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z" />
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 15v2m4-2v2m4-2v2" />
              </svg>`,
        tagline: "Snow day! Perfect excuse for hot cocoa and hot code."
    },
    default: {
        borderBgClasses: 'border-white/20 bg-white/10',
        icon: `<svg class="w-12 h-12 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
              </svg>`,
        tagline: "Weather's here—let's get moving."
    }
};

function getWeatherCondition(description) {
    const desc = description.toLowerCase();
    if (desc.includes('sun') || desc.includes('clear')) return 'sunny';
    if (desc.includes('cloud')) return 'cloudy';
    if (desc.includes('rain')) return 'rain';
    if (desc.includes('snow')) return 'snow';
    return 'default';
}

function WeatherCard({ nextMeeting, forecastTime, temperature, description }) {
    const condition = getWeatherCondition(description);
    const { borderBgClasses, icon, tagline } = weatherConditions[condition] || weatherConditions.default;

    return `
        <div class="border rounded-xl p-6 mt-8 max-w-md mx-auto flex flex-col items-center space-y-4 ${borderBgClasses}">
            <div class="flex items-center space-x-4">
                ${icon}
                <h2 class="text-5xl font-bold">${temperature}°F</h2>
            </div>
            <p class="italic text-gray-200">${tagline}</p>
            <ul class="list-disc list-inside space-y-1 text-gray-200">
                <li><strong>Next Meeting:</strong> ${nextMeeting}</li>
                <li><strong>Forecast Time:</strong> ${forecastTime}</li>
            </ul>
        </div>
    `;
}

export default WeatherCard; 