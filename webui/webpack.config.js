'use strict';

const path = require('path');
const webpack = require('webpack');
const AotPlugin = require('@ngtools/webpack').AngularCompilerPlugin;
const rootDir = path.resolve(__dirname);

function root(args) {
  args = Array.prototype.slice.call(arguments, 0);
  return path.join.apply(path, [rootDir].concat(args));
}

const config = {
  entry: {
    'vendor': './src/vendor',
    'app': './src/bootstrap'
  },
  output: {
    path: path.resolve(__dirname, './dist'),
    publicPath: "/assets/",
    filename: '[name].bundle.js'
  },
  resolve: {
    extensions: ['.ts', '.js', '.css']
  },
  module: {
    rules: [
      { enforce: 'pre', test: /\.ts$/, exclude: /node_modules/, loader: 'tslint-loader' },
      { test: /\.ts$/, exclude: /node_modules/, loader: 'awesome-typescript-loader' },
      { test: /\.css$/, loader: 'style-loader!css-loader' },
      { test: /\.woff2?$/, loader: 'url-loader?name=dist/fonts/[name].[ext]&limit=10000&mimetype=application/font-woff' },
      { test: /\.(ttf|eot|svg)$/, loader: 'file-loader?name=dist/fonts/[name].[ext]' }
    ]
  },
  plugins: [
    // Fixes Angular 2 error
    new webpack.ContextReplacementPlugin(
      /angular(\\|\/)core(\\|\/)(esm(\\|\/)src|src)(\\|\/)linker/,
      __dirname
    ),
  ],
  devServer: {
    noInfo: true,
    hot: true,
    inline: true,
    historyApiFallback: true
  }
};

if (!(process.env.WEBPACK_ENV === 'production')) {
  config.devtool = 'source-map';
  config.plugins = config.plugins.concat([
    new webpack.DefinePlugin({
      'WEBPACK_ENV': '"dev"'
    })
  ])
} else {
  config.devtool = 'hidden-source-map';
  config.module.rules = [
    { test: /(?:\.ngfactory\.js|\.ngstyle\.js|\.ts)$/, loaders: ['@ngtools/webpack'] },
    { test: /\.css$/, loader: 'style-loader!css-loader' }
  ];
  config.plugins = config.plugins.concat([
    new AotPlugin({
      tsConfigPath: root('tsconfig-aot.json'),
      basePath: root(''),
      entryModule: root('src', 'app', 'app.module#AppModule'),
      mainPath: root('src', 'bootstrap.ts'),
      i18nInFile: "src/locale/messages.en.xlf",
      i18nInFormat: "xlf",
      locale: "en"
    }),
    new webpack.optimize.UglifyJsPlugin({
      sourceMap: true,
      beautify: false,
      mangle: {
        screw_ie8: true
      },
      compress: {
        unused: true,
        dead_code: true,
        drop_debugger: true,
        conditionals: true,
        evaluate: true,
        drop_console: true,
        sequences: true,
        booleans: true,
        screw_ie8: true,
        warnings: false
      },
      comments: false
    }),
    new webpack.DefinePlugin({
      'WEBPACK_ENV': '"production"'
    }),
  ]);
}

module.exports = config;