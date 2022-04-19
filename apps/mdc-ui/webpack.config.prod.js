const { merge } = require('webpack-merge');
const common = require('./webpack.config');
const path = require('path');
const HtmlWebpackPlugin = require("html-webpack-plugin");

const outputPath = path.resolve(__dirname, 'dist');
const prodConfig = {
  output: {
    path: outputPath,
    filename: '[name]-[contenthash].js',
    publicPath: '/js/assets',
  },
  mode: 'production',
  plugins: [
    new HtmlWebpackPlugin({
      templateContent: ({ htmlWebpackPlugin }) => {
        return JSON.stringify({
          ...htmlWebpackPlugin.files,
        });
      },
      inject: false,
      filename: 'main-assets.json', // it will be in outputPath
      chunks: 'all',
    }),
  ],
};

module.exports = merge(common.config, prodConfig);
