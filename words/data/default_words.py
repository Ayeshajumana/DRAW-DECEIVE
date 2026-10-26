"""
Default curated word dataset with 160+ words for DRAW & DECEIVE.
Categories: animals, food, objects, nature, sports, entertainment, tech, activities.
Difficulties: easy, medium, hard.
"""

INITIAL_WORDS = [
    # Animals - Easy
    {"text": "cat", "category": "animals", "difficulty": "easy", "hint": "Purrs and chases mice"},
    {"text": "dog", "category": "animals", "difficulty": "easy", "hint": "Man's best friend"},
    {"text": "fish", "category": "animals", "difficulty": "easy", "hint": "Swims in water"},
    {"text": "duck", "category": "animals", "difficulty": "easy", "hint": "Quacks and waddles"},
    {"text": "lion", "category": "animals", "difficulty": "easy", "hint": "King of the jungle"},
    {"text": "bear", "category": "animals", "difficulty": "easy", "hint": "Loves honey and hibernates"},
    {"text": "frog", "category": "animals", "difficulty": "easy", "hint": "Green and jumps"},
    {"text": "pig", "category": "animals", "difficulty": "easy", "hint": "Oinks in the mud"},
    # Animals - Medium
    {"text": "giraffe", "category": "animals", "difficulty": "medium", "hint": "Has an extremely long neck"},
    {"text": "penguin", "category": "animals", "difficulty": "medium", "hint": "Tuxedo bird that cannot fly"},
    {"text": "kangaroo", "category": "animals", "difficulty": "medium", "hint": "Carries baby in a pouch"},
    {"text": "octopus", "category": "animals", "difficulty": "medium", "hint": "Has eight tentacles and ink"},
    {"text": "dolphin", "category": "animals", "difficulty": "medium", "hint": "Playful and intelligent sea mammal"},
    {"text": "cheetah", "category": "animals", "difficulty": "medium", "hint": "Fastest land animal with spots"},
    {"text": "elephant", "category": "animals", "difficulty": "medium", "hint": "Huge ears and a trunk"},
    {"text": "crocodile", "category": "animals", "difficulty": "medium", "hint": "Reptile with sharp teeth in rivers"},
    # Animals - Hard
    {"text": "chameleon", "category": "animals", "difficulty": "hard", "hint": "Changes color to blend in"},
    {"text": "platypus", "category": "animals", "difficulty": "hard", "hint": "Egg-laying mammal with a duck bill"},
    {"text": "hedgehog", "category": "animals", "difficulty": "hard", "hint": "Small mammal covered in spines"},
    {"text": "flamingo", "category": "animals", "difficulty": "hard", "hint": "Pink wading bird standing on one leg"},

    # Food & Drinks - Easy
    {"text": "apple", "category": "food", "difficulty": "easy", "hint": "Keeps the doctor away"},
    {"text": "banana", "category": "food", "difficulty": "easy", "hint": "Yellow curved fruit monkeys love"},
    {"text": "pizza", "category": "food", "difficulty": "easy", "hint": "Cheesy Italian sliced pie"},
    {"text": "burger", "category": "food", "difficulty": "easy", "hint": "Beef patty in a bun"},
    {"text": "ice cream", "category": "food", "difficulty": "easy", "hint": "Frozen sweet dessert in a cone"},
    {"text": "egg", "category": "food", "difficulty": "easy", "hint": "Laid by birds with yolk inside"},
    {"text": "donut", "category": "food", "difficulty": "easy", "hint": "Fried dough ring with sprinkles"},
    {"text": "cookie", "category": "food", "difficulty": "easy", "hint": "Baked sweet treat with chocolate chips"},
    # Food & Drinks - Medium
    {"text": "spaghetti", "category": "food", "difficulty": "medium", "hint": "Long noodles with tomato sauce"},
    {"text": "sushi", "category": "food", "difficulty": "medium", "hint": "Japanese rice roll wrapped in seaweed"},
    {"text": "popcorn", "category": "food", "difficulty": "medium", "hint": "Corn kernels popped at movies"},
    {"text": "pancake", "category": "food", "difficulty": "medium", "hint": "Flat breakfast cake topped with syrup"},
    {"text": "taco", "category": "food", "difficulty": "medium", "hint": "Folded tortilla filled with meat and salsa"},
    {"text": "hot dog", "category": "food", "difficulty": "medium", "hint": "Sausage in a long sliced bun"},
    {"text": "croissant", "category": "food", "difficulty": "medium", "hint": "Flaky French buttery crescent pastry"},
    {"text": "cupcake", "category": "food", "difficulty": "medium", "hint": "Small individual cake with frosting"},
    # Food & Drinks - Hard
    {"text": "pineapple", "category": "food", "difficulty": "hard", "hint": "Tropical prickly fruit with crown leaves"},
    {"text": "watermelon", "category": "food", "difficulty": "hard", "hint": "Large green melon with red seeded center"},
    {"text": "burrito", "category": "food", "difficulty": "hard", "hint": "Large wrapped flour tortilla cylinder"},
    {"text": "cheesecake", "category": "food", "difficulty": "hard", "hint": "Rich dessert made with cream cheese"},

    # Objects & Tools - Easy
    {"text": "chair", "category": "objects", "difficulty": "easy", "hint": "You sit on it with four legs"},
    {"text": "clock", "category": "objects", "difficulty": "easy", "hint": "Tells time on the wall"},
    {"text": "book", "category": "objects", "difficulty": "easy", "hint": "Has pages and stories to read"},
    {"text": "pencil", "category": "objects", "difficulty": "easy", "hint": "Used for writing with graphite and eraser"},
    {"text": "cup", "category": "objects", "difficulty": "easy", "hint": "Container for drinking beverages"},
    {"text": "hat", "category": "objects", "difficulty": "easy", "hint": "Worn on top of the head"},
    {"text": "shoe", "category": "objects", "difficulty": "easy", "hint": "Worn on the foot"},
    {"text": "key", "category": "objects", "difficulty": "easy", "hint": "Unlocks doors and locks"},
    # Objects & Tools - Medium
    {"text": "scissors", "category": "objects", "difficulty": "medium", "hint": "Two blades used for cutting paper"},
    {"text": "umbrella", "category": "objects", "difficulty": "medium", "hint": "Protects you from rain"},
    {"text": "guitar", "category": "objects", "difficulty": "medium", "hint": "Six-stringed acoustic musical instrument"},
    {"text": "hammer", "category": "objects", "difficulty": "medium", "hint": "Tool used to drive nails into wood"},
    {"text": "backpack", "category": "objects", "difficulty": "medium", "hint": "Bag carried on your shoulders"},
    {"text": "flashlight", "category": "objects", "difficulty": "medium", "hint": "Portable electric hand torch"},
    {"text": "camera", "category": "objects", "difficulty": "medium", "hint": "Captures photos and memories"},
    {"text": "glasses", "category": "objects", "difficulty": "medium", "hint": "Lenses worn to improve eyesight"},
    # Objects & Tools - Hard
    {"text": "microscope", "category": "objects", "difficulty": "hard", "hint": "Magnifies tiny cells in science labs"},
    {"text": "telescope", "category": "objects", "difficulty": "hard", "hint": "Used to view distant stars and planets"},
    {"text": "compass", "category": "objects", "difficulty": "hard", "hint": "Navigation tool pointing to magnetic north"},
    {"text": "hourglass", "category": "objects", "difficulty": "hard", "hint": "Sand trickling down to measure time"},

    # Nature & Weather - Easy
    {"text": "sun", "category": "nature", "difficulty": "easy", "hint": "Bright star giving light and heat"},
    {"text": "moon", "category": "nature", "difficulty": "easy", "hint": "Orbits Earth and shines at night"},
    {"text": "tree", "category": "nature", "difficulty": "easy", "hint": "Tall plant with trunk and leaves"},
    {"text": "flower", "category": "nature", "difficulty": "easy", "hint": "Colorful blossom with petals"},
    {"text": "cloud", "category": "nature", "difficulty": "easy", "hint": "Fluffy white water vapor in the sky"},
    {"text": "rain", "category": "nature", "difficulty": "easy", "hint": "Water falling from clouds"},
    {"text": "star", "category": "nature", "difficulty": "easy", "hint": "Twinkles in the night sky"},
    {"text": "fire", "category": "nature", "difficulty": "easy", "hint": "Produces flames, heat, and smoke"},
    # Nature & Weather - Medium
    {"text": "rainbow", "category": "nature", "difficulty": "medium", "hint": "Multi-colored arc after the rain"},
    {"text": "mountain", "category": "nature", "difficulty": "medium", "hint": "Large natural elevation with a snowy peak"},
    {"text": "volcano", "category": "nature", "difficulty": "medium", "hint": "Mountain that erupts hot lava"},
    {"text": "waterfall", "category": "nature", "difficulty": "medium", "hint": "River cascading over a steep cliff"},
    {"text": "lightning", "category": "nature", "difficulty": "medium", "hint": "Electric flash during a thunderstorm"},
    {"text": "island", "category": "nature", "difficulty": "medium", "hint": "Land completely surrounded by water"},
    {"text": "tornado", "category": "nature", "difficulty": "medium", "hint": "Violently rotating column of air"},
    {"text": "desert", "category": "nature", "difficulty": "medium", "hint": "Dry sandy wasteland with cacti"},
    # Nature & Weather - Hard
    {"text": "aurora", "category": "nature", "difficulty": "hard", "hint": "Northern lights glowing in the polar sky"},
    {"text": "avalanche", "category": "nature", "difficulty": "hard", "hint": "Mass of snow rapidly sliding down a mountain"},
    {"text": "iceberg", "category": "nature", "difficulty": "hard", "hint": "Massive floating chunk of ice in the ocean"},
    {"text": "coral reef", "category": "nature", "difficulty": "hard", "hint": "Underwater colorful marine ecosystem"},

    # Sports & Games - Easy
    {"text": "football", "category": "sports", "difficulty": "easy", "hint": "Ball kicked into a goal net"},
    {"text": "basketball", "category": "sports", "difficulty": "easy", "hint": "Orange ball bounced and thrown into a hoop"},
    {"text": "swimming", "category": "sports", "difficulty": "easy", "hint": "Moving through water using arms and legs"},
    {"text": "running", "category": "sports", "difficulty": "easy", "hint": "Moving fast on feet in a race"},
    {"text": "bowling", "category": "sports", "difficulty": "easy", "hint": "Rolling a heavy ball to knock down 10 pins"},
    {"text": "golf", "category": "sports", "difficulty": "easy", "hint": "Hitting a small ball into a hole with a club"},
    {"text": "boxing", "category": "sports", "difficulty": "easy", "hint": "Fighting in a ring with padded gloves"},
    {"text": "cycling", "category": "sports", "difficulty": "easy", "hint": "Riding a bicycle with pedals"},
    # Sports & Games - Medium
    {"text": "tennis", "category": "sports", "difficulty": "medium", "hint": "Hitting a yellow ball over a net with racquets"},
    {"text": "baseball", "category": "sports", "difficulty": "medium", "hint": "Hitting a pitched ball with a wooden bat"},
    {"text": "skateboard", "category": "sports", "difficulty": "medium", "hint": "Board on four wheels for tricks"},
    {"text": "archery", "category": "sports", "difficulty": "medium", "hint": "Shooting arrows at a bullseye target"},
    {"text": "chess", "category": "sports", "difficulty": "medium", "hint": "Strategy board game with king and queen"},
    {"text": "skiing", "category": "sports", "difficulty": "medium", "hint": "Gliding on snow wearing long narrow boards"},
    {"text": "surfing", "category": "sports", "difficulty": "medium", "hint": "Riding ocean waves standing on a board"},
    {"text": "volleyball", "category": "sports", "difficulty": "medium", "hint": "Spiking a ball over a high net on sand"},
    # Sports & Games - Hard
    {"text": "gymnastics", "category": "sports", "difficulty": "hard", "hint": "Acrobatic flips on balance beams and bars"},
    {"text": "fencing", "category": "sports", "difficulty": "hard", "hint": "Sword dueling wearing white protective masks"},
    {"text": "bobsled", "category": "sports", "difficulty": "hard", "hint": "Gravity-powered sled sliding down ice track"},
    {"text": "curling", "category": "sports", "difficulty": "hard", "hint": "Sliding stones on ice while sweeping with brooms"},

    # Entertainment & Pop Culture - Easy
    {"text": "music", "category": "entertainment", "difficulty": "easy", "hint": "Notes, songs, and melodies"},
    {"text": "movie", "category": "entertainment", "difficulty": "easy", "hint": "Film watched on a giant cinema screen"},
    {"text": "dance", "category": "entertainment", "difficulty": "easy", "hint": "Moving body rhythmically to a beat"},
    {"text": "clown", "category": "entertainment", "difficulty": "easy", "hint": "Circus performer with red nose and makeup"},
    {"text": "magic", "category": "entertainment", "difficulty": "easy", "hint": "Illusions and pulling rabbits from hats"},
    {"text": "circus", "category": "entertainment", "difficulty": "easy", "hint": "Show with acrobats under a big top tent"},
    {"text": "video game", "category": "entertainment", "difficulty": "easy", "hint": "Interactive game played on screen with controller"},
    {"text": "superhero", "category": "entertainment", "difficulty": "easy", "hint": "Hero with a cape saving the day"},
    # Entertainment & Pop Culture - Medium
    {"text": "pirate", "category": "entertainment", "difficulty": "medium", "hint": "Sails ships with eye patch and parrot"},
    {"text": "astronaut", "category": "entertainment", "difficulty": "medium", "hint": "Travels in spacesuit into outer space"},
    {"text": "vampire", "category": "entertainment", "difficulty": "medium", "hint": "Creature of the night that drinks blood"},
    {"text": "zombie", "category": "entertainment", "difficulty": "medium", "hint": "Undead creature craving brains"},
    {"text": "mermaid", "category": "entertainment", "difficulty": "medium", "hint": "Mythical creature half human half fish"},
    {"text": "alien", "category": "entertainment", "difficulty": "medium", "hint": "Being from another planet in a UFO"},
    {"text": "castle", "category": "entertainment", "difficulty": "medium", "hint": "Fortified medieval palace with towers"},
    {"text": "roller coaster", "category": "entertainment", "difficulty": "medium", "hint": "Thrilling amusement park ride with loops"},
    # Entertainment & Pop Culture - Hard
    {"text": "puppet", "category": "entertainment", "difficulty": "hard", "hint": "Figure manipulated by strings or hand"},
    {"text": "carnival", "category": "entertainment", "difficulty": "hard", "hint": "Festive celebration with parades and masks"},
    {"text": "orchestra", "category": "entertainment", "difficulty": "hard", "hint": "Large instrumental ensemble with conductor"},
    {"text": "treasure chest", "category": "entertainment", "difficulty": "hard", "hint": "Locked wooden box packed with gold coins"},

    # Technology & Science - Easy
    {"text": "phone", "category": "tech", "difficulty": "easy", "hint": "Handheld device for calls and apps"},
    {"text": "computer", "category": "tech", "difficulty": "easy", "hint": "Screen, keyboard, and processor for digital tasks"},
    {"text": "robot", "category": "tech", "difficulty": "easy", "hint": "Mechanical being programmed to do tasks"},
    {"text": "rocket", "category": "tech", "difficulty": "easy", "hint": "Propelled into space by fire engines"},
    {"text": "television", "category": "tech", "difficulty": "easy", "hint": "Screen for broadcasting shows and news"},
    {"text": "car", "category": "tech", "difficulty": "easy", "hint": "Four-wheeled motor vehicle on roads"},
    {"text": "airplane", "category": "tech", "difficulty": "easy", "hint": "Vehicle with wings flying through skies"},
    {"text": "lightbulb", "category": "tech", "difficulty": "easy", "hint": "Glows with electricity to illuminate rooms"},
    # Technology & Science - Medium
    {"text": "headphones", "category": "tech", "difficulty": "medium", "hint": "Worn over ears to listen privately to audio"},
    {"text": "battery", "category": "tech", "difficulty": "medium", "hint": "Stores chemical energy into electric power"},
    {"text": "drone", "category": "tech", "difficulty": "medium", "hint": "Remote-controlled unmanned flying quadcopter"},
    {"text": "satellite", "category": "tech", "difficulty": "medium", "hint": "Orbits Earth transmitting GPS and data"},
    {"text": "laptop", "category": "tech", "difficulty": "medium", "hint": "Portable folding personal computer"},
    {"text": "solar panel", "category": "tech", "difficulty": "medium", "hint": "Converts sunlight directly into clean energy"},
    {"text": "magnet", "category": "tech", "difficulty": "medium", "hint": "Attracts iron with north and south poles"},
    {"text": "submarine", "category": "tech", "difficulty": "medium", "hint": "Naval vessel operating deep underwater"},
    # Technology & Science - Hard
    {"text": "space station", "category": "tech", "difficulty": "hard", "hint": "Laboratory orbiting Earth where astronauts live"},
    {"text": "3D printer", "category": "tech", "difficulty": "hard", "hint": "Builds physical objects layer by layer"},
    {"text": "virtual reality", "category": "tech", "difficulty": "hard", "hint": "Headset creating immersive 3D simulations"},
    {"text": "hologram", "category": "tech", "difficulty": "hard", "hint": "Three-dimensional image formed by light beams"},

    # Everyday Activities - Easy
    {"text": "sleeping", "category": "activities", "difficulty": "easy", "hint": "Resting in bed with eyes closed"},
    {"text": "cooking", "category": "activities", "difficulty": "easy", "hint": "Preparing food with pans and stove"},
    {"text": "reading", "category": "activities", "difficulty": "easy", "hint": "Looking at words in a book"},
    {"text": "drawing", "category": "activities", "difficulty": "easy", "hint": "Making pictures with a pencil or brush"},
    {"text": "eating", "category": "activities", "difficulty": "easy", "hint": "Consuming food with mouth and fork"},
    {"text": "walking", "category": "activities", "difficulty": "easy", "hint": "Moving forward step by step on foot"},
    {"text": "singing", "category": "activities", "difficulty": "easy", "hint": "Making musical sounds with the voice"},
    {"text": "laughing", "category": "activities", "difficulty": "easy", "hint": "Expressing amusement and joy out loud"},
    # Everyday Activities - Medium
    {"text": "fishing", "category": "activities", "difficulty": "medium", "hint": "Catching fish using rod and bait"},
    {"text": "gardening", "category": "activities", "difficulty": "medium", "hint": "Planting seeds and tending flowers"},
    {"text": "shopping", "category": "activities", "difficulty": "medium", "hint": "Pushing a cart and buying items in stores"},
    {"text": "camping", "category": "activities", "difficulty": "medium", "hint": "Sleeping outdoors in a tent near a campfire"},
    {"text": "brushing teeth", "category": "activities", "difficulty": "medium", "hint": "Cleaning teeth with paste and toothbrush"},
    {"text": "baking", "category": "activities", "difficulty": "medium", "hint": "Making bread and cakes inside an oven"},
    {"text": "painting", "category": "activities", "difficulty": "medium", "hint": "Applying colorful paints onto a canvas"},
    {"text": "climbing", "category": "activities", "difficulty": "medium", "hint": "Ascending up a rock wall or mountain"},
    # Everyday Activities - Hard
    {"text": "skydiving", "category": "activities", "difficulty": "hard", "hint": "Jumping out of an airplane with a parachute"},
    {"text": "scuba diving", "category": "activities", "difficulty": "hard", "hint": "Swimming deep underwater with an oxygen tank"},
    {"text": "juggling", "category": "activities", "difficulty": "hard", "hint": "Keeping multiple balls tossed continuously in the air"},
    {"text": "ice skating", "category": "activities", "difficulty": "hard", "hint": "Gliding across frozen ice rink on bladed boots"},
]
