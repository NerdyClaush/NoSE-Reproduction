var Table = require('mysql-faker').Table,
    insert = require('mysql-faker').insert;

function intEnv(name, fallback) {
  var value = process.env[name];
  return value ? parseInt(value, 10) : fallback;
}

var counts = {
  categories: intEnv('RUBIS_CATEGORIES', 500),
  regions: intEnv('RUBIS_REGIONS', 50),
  users: intEnv('RUBIS_USERS', 1000),
  items: intEnv('RUBIS_ITEMS', 5000),
  bids: intEnv('RUBIS_BIDS', 20000),
  comments: intEnv('RUBIS_COMMENTS', 10000),
  buy_now: intEnv('RUBIS_BUYNOW', 5000)
};

console.log('Generating RUBiS data with counts:', counts);

var categories = (new Table('categories', counts.categories));
categories.lorem_words('name', 2);

var regions = (new Table('regions', counts.regions));
regions.lorem_words('name', 2);

var users = (new Table('users', counts.users));
users.name_firstName('firstname')
     .name_lastName('lastname')
     .random_uuid('nickname')
     .internet_password('password')
     .internet_email('email')
     .random_number('rating', {min: -50, max: 200})
     .finance_amount('balance')
     .date_past('creation_date')
     .random_number('region', {min: 1, max: regions.count});

var items = (new Table('items', counts.items));
items.lorem_words('name')
     .lorem_paragraph('description')
     .finance_amount('initial_price')
     .random_number('quantity', {min: 0, max: 10})
     .finance_amount('reserve_price')
     .finance_amount('buy_now')
     .random_number('nb_of_bids', {min: 0, max: 100})
     .finance_amount('max_bid')
     .date_past('start_date')
     .date_past('end_date')
     .random_number('seller', {min: 1, max: users.count})
     .random_number('category', {min: 1, max: categories.count});

var bids = (new Table('bids', counts.bids));
bids.random_number('qty', {min: 1, max: 5})
    .finance_amount('bid')
    .finance_amount('max_bid')
    .date_past('date')
    .random_number('user', {min: 1, max: users.count})
    .random_number('item', {min: 1, max: items.count});

var comments = (new Table('comments', counts.comments));
comments.random_number('rating', {min: -5, max: 5})
        .date_past('date')
        .lorem_sentences('comment')
        .random_number('from_user', {min: 1, max: users.count})
        .random_number('to_user', {min: 1, max: users.count})
        .random_number('item', {min: 1, max: items.count});

var buy_now = (new Table('buynow', counts.buy_now));
buy_now.random_number('qty', {min: 1, max: 3})
       .date_past('date')
       .random_number('buyer', {min: 1, max: users.count})
       .random_number('item', {min: 1, max: items.count});

insert([
  categories,
  regions,
  users,
  items,
  bids,
  comments,
  buy_now
], {
  host: process.env.RUBIS_MYSQL_HOST || 'localhost',
  user: process.env.RUBIS_MYSQL_USER || 'root',
  password: process.env.RUBIS_MYSQL_PASSWORD || 'root',
  database: process.env.RUBIS_MYSQL_DATABASE || 'rubis'
}, true);

