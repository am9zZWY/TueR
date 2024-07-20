const colors = require('tailwindcss/colors')

/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{vue,js,ts,jsx,tsx}'
  ],
  theme: {
    colors: {
      transparent: 'transparent',
      current: 'currentColor',
      primary: {
        '50': '#fef2f2',
        '100': '#fde6e7',
        '200': '#fad1d4',
        '300': '#f6abb0',
        '400': '#f07c86',
        '500': '#e54e5f',
        '600': '#d12d47',
        '700': '#a51e37',
        '800': '#941d37',
        '900': '#7e1d35',
        '950': '#460b19'
      },
      secondary: {
        '50': '#f7f5ef',
        '100': '#ebe8d6',
        '200': '#d8d0b0',
        '300': '#c2b482',
        '400': '#b4a069',
        '500': '#a08852',
        '600': '#896f45',
        '700': '#6f5539',
        '800': '#5e4835',
        '900': '#523f31',
        '950': '#2e221a'
      },
      tertiary: {
        '50': '#f5f6f9',
        '100': '#e7eaf2',
        '200': '#d5dae8',
        '300': '#b8c2d8',
        '400': '#95a3c5',
        '500': '#7b88b6',
        '600': '#6973a7',
        '700': '#5d6398',
        '800': '#50537d',
        '900': '#434665',
        '950': '#2c2d3f',
      },

      black: colors.black,
      white: colors.white,
      gray: colors.gray,
      emerald: colors.emerald,
      indigo: colors.indigo,
      yellow: colors.yellow,
    },
    fontFamily: {
      body: ['Nunito']
    }
  },
  plugins: []
}
