const path = require('path');

module.exports = {
  entry: './src/index.js',
  output: {
    path: path.resolve(__dirname, '../static/js'),
    filename: 'kibray-navigation.js',
    publicPath: '/static/js/'
  },
  module: {
    rules: [
      {
        test: /\.(js|jsx)$/,
        exclude: /node_modules/,
        use: {
          loader: 'babel-loader',
          options: {
            presets: ['@babel/preset-react', ['@babel/preset-env', { targets: 'defaults' }]]
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
     fullySpecified: false
  }
};
