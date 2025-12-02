const path = require('path');
const webpack = require('webpack');
const { InjectManifest } = require('workbox-webpack-plugin');

module.exports = {
  mode: process.env.NODE_ENV === 'production' ? 'production' : 'development',
  entry: './src/index.js',
  output: {
    path: path.resolve(__dirname, '../../static/js'),
    filename: 'kibray-navigation.js',
    publicPath: '/static/js/',
    clean: true
  },
  plugins: [
    new webpack.DefinePlugin({
      'process.env.NODE_ENV': JSON.stringify(process.env.NODE_ENV || 'production'),
      'process.env': '{}'
    }),
    new webpack.ProvidePlugin({
      process: 'process/browser'
    }),
    // Workbox service worker plugin for PWA
    ...(process.env.NODE_ENV === 'production' ? [
      new InjectManifest({
        swSrc: './src/service-worker.js',
        swDest: '../../static/js/service-worker.js',
        exclude: [/\.pdf$/, /\.map$/, /^manifest.*\.js$/],
        maximumFileSizeToCacheInBytes: 5 * 1024 * 1024, // 5MB
      })
    ] : [])
  ],
  module: {
    rules: [
      {
        test: /\.(js|jsx)$/,
        exclude: /node_modules/,
        use: {
          loader: 'babel-loader',
          options: {
            presets: [
              '@babel/preset-react',
              ['@babel/preset-env', { 
                targets: 'defaults',
                modules: false
              }]
            ]
          }
        }
      },
      {
        test: /\.css$/,
        use: ['style-loader', 'css-loader']
      }
    ]
  },
  resolve: {
    extensions: ['.js', '.jsx'],
    fallback: {
      "process/browser": require.resolve("process/browser.js")
    }
  },
  performance: {
    maxAssetSize: 512000,
    maxEntrypointSize: 512000,
    hints: 'warning'
  },
  optimization: {
    minimize: true
  }
};

